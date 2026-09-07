from pathlib import Path
import operator
import sqlite3

import numpy as np
import pandas as pd
import yaml


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DB_PATH = PROJECT_ROOT / "data" / "nifty100.db"
CONFIG_PATH = PROJECT_ROOT / "config" / "screener_config.yaml"


# ============================================================
# OPERATORS
# ============================================================

OPERATORS = {
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
    "==": operator.eq,
}


# ============================================================
# SCREENER ENGINE
# ============================================================

class ScreenerEngine:

    def __init__(
        self,
        db_path=DB_PATH,
        config_path=CONFIG_PATH
    ):
        self.db_path = Path(db_path)
        self.config_path = Path(config_path)

        self.config = self._load_config()

    # ========================================================
    # CONFIGURATION
    # ========================================================

    def _load_config(self):

        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found:\n"
                f"{self.config_path}"
            )

        with open(
            self.config_path,
            "r",
            encoding="utf-8"
        ) as file:

            config = yaml.safe_load(file)

        if not config:
            raise ValueError(
                "screener_config.yaml is empty."
            )

        return config

    # ========================================================
    # DATABASE
    # ========================================================

    def _connect(self):

        if not self.db_path.exists():
            raise FileNotFoundError(
                f"Database not found:\n"
                f"{self.db_path}"
            )

        conn = sqlite3.connect(
            self.db_path
        )

        conn.execute(
            "PRAGMA foreign_keys = ON"
        )

        return conn

    # ========================================================
    # LOAD LATEST DATA
    # ========================================================

    def load_data(self):

        conn = self._connect()

        query = """
        WITH latest_ratios AS (
            SELECT *
            FROM financial_ratios fr
            WHERE year = (
                SELECT MAX(fr2.year)
                FROM financial_ratios fr2
                WHERE fr2.company_id = fr.company_id
            )
        ),

        latest_pl AS (
            SELECT *
            FROM profitandloss p
            WHERE year = (
                SELECT MAX(p2.year)
                FROM profitandloss p2
                WHERE p2.company_id = p.company_id
            )
        ),

        latest_market AS (
            SELECT *
            FROM market_cap m
            WHERE year = (
                SELECT MAX(m2.year)
                FROM market_cap m2
                WHERE m2.company_id = m.company_id
            )
        )

        SELECT

            c.id AS company_id,
            c.company_name,

            s.broad_sector,
            s.sub_sector,

            -- Profitability
            r.return_on_equity,
            r.return_on_capital,
            r.return_on_assets,
            r.net_profit_margin,
            r.operating_profit_margin,

            -- Leverage
            r.debt_to_equity,
            r.interest_coverage,
            r.icr_label,

            -- Cash flow
            r.free_cash_flow,
            r.cash_from_operations_cr,
            r.capex_cr,

            -- Growth
            r.revenue_cagr,
            r.revenue_cagr_3yr,
            r.revenue_cagr_5yr,
            r.revenue_cagr_10yr,

            r.pat_cagr,
            r.pat_cagr_3yr,
            r.pat_cagr_5yr,
            r.pat_cagr_10yr,

            r.eps_cagr,
            r.eps_cagr_3yr,
            r.eps_cagr_5yr,
            r.eps_cagr_10yr,

            -- Other ratios
            r.asset_turnover,
            r.earnings_per_share,
            r.book_value_per_share,
            r.dividend_payout_ratio_pct,

            -- Debt
            r.total_debt_cr,

            -- P&L
            p.sales,
            p.net_profit,
            p.eps,

            -- Market data
            m.market_cap_crore,
            m.enterprise_value_crore,
            m.pe_ratio,
            m.pb_ratio,
            m.ev_ebitda,
            m.dividend_yield_pct,

            -- Sprint 2 score kept only for reference
            r.composite_quality_score
                AS previous_composite_quality_score

        FROM companies c

        LEFT JOIN sectors s
            ON c.id = s.company_id

        LEFT JOIN latest_ratios r
            ON c.id = r.company_id

        LEFT JOIN latest_pl p
            ON c.id = p.company_id

        LEFT JOIN latest_market m
            ON c.id = m.company_id

        ORDER BY c.company_name
        """

        df = pd.read_sql_query(
            query,
            conn
        )

        conn.close()

        # Remove accidental duplicate companies
        df = df.drop_duplicates(
            subset=["company_id"],
            keep="first"
        )

        return df.reset_index(drop=True)

    # ========================================================
    # OPERATOR
    # ========================================================

    @staticmethod
    def _apply_operator(
        series,
        operator_symbol,
        threshold
    ):

        if operator_symbol not in OPERATORS:
            raise ValueError(
                f"Unsupported operator: "
                f"{operator_symbol}"
            )

        return OPERATORS[
            operator_symbol
        ](
            series,
            threshold
        )

    # ========================================================
    # D/E FILTER
    # ========================================================

    def _apply_de_filter(
        self,
        df,
        threshold,
        operator_symbol
    ):

        financial_mask = (
            df["broad_sector"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.lower()
            .eq("financials")
        )

        valid_de = (
            df["debt_to_equity"].notna()
        )

        normal_mask = pd.Series(
            False,
            index=df.index
        )

        eligible = (
            ~financial_mask
            & valid_de
        )

        if eligible.any():

            normal_mask.loc[eligible] = (
                self._apply_operator(
                    df.loc[
                        eligible,
                        "debt_to_equity"
                    ],
                    operator_symbol,
                    threshold
                )
            )

        # Financial companies bypass D/E filter
        final_mask = (
            financial_mask
            | normal_mask
        )

        return final_mask

    # ========================================================
    # D/E DECLINING
    # ========================================================

    def _filter_de_declining(
        self,
        df
    ):

        conn = self._connect()

        query = """
        SELECT
            company_id,
            year,
            debt_to_equity
        FROM financial_ratios
        ORDER BY company_id, year
        """

        history = pd.read_sql_query(
            query,
            conn
        )

        conn.close()

        result = pd.Series(
            False,
            index=df.index
        )

        if history.empty:
            return result

        history = history.sort_values(
            ["company_id", "year"]
        )

        for company_id, group in history.groupby(
            "company_id"
        ):

            group = group.dropna(
                subset=["debt_to_equity"]
            ).sort_values("year")

            if len(group) < 2:
                continue

            previous_de = (
                group.iloc[-2]["debt_to_equity"]
            )

            latest_de = (
                group.iloc[-1]["debt_to_equity"]
            )

            if latest_de < previous_de:

                result.loc[
                    df["company_id"] == company_id
                ] = True

        return result

    # ========================================================
    # APPLY FILTERS
    # ========================================================

    def apply_filters(
        self,
        df,
        thresholds
    ):

        result = df.copy()

        filter_definitions = (
            self.config.get(
                "filters",
                {}
            )
        )

        for filter_name, threshold in thresholds.items():

            # ------------------------------------------------
            # D/E DECLINING
            # ------------------------------------------------

            if filter_name == "de_declining":

                if threshold:

                    mask = (
                        self._filter_de_declining(
                            result
                        )
                    )

                    result = result.loc[
                        mask
                    ]

                continue

            # ------------------------------------------------
            # DIVIDEND PAYOUT MAX
            # ------------------------------------------------

            if filter_name == "dividend_payout_max":

                column = (
                    "dividend_payout_ratio_pct"
                )

                if column not in result.columns:
                    raise KeyError(
                        "Dividend payout column "
                        "is not available."
                    )

                mask = (
                    result[column].notna()
                    &
                    (
                        result[column]
                        <= threshold
                    )
                )

                result = result.loc[
                    mask
                ]

                continue

            # ------------------------------------------------
            # REVENUE CAGR 3YR
            # ------------------------------------------------

            if filter_name == "revenue_cagr_3yr_min":

                column = "revenue_cagr_3yr"
                operator_symbol = ">="

            # ------------------------------------------------
            # NORMAL CONFIGURED FILTER
            # ------------------------------------------------

            else:

                if filter_name not in filter_definitions:

                    raise KeyError(
                        f"Filter '{filter_name}' "
                        f"is not defined in "
                        f"screener_config.yaml."
                    )

                definition = (
                    filter_definitions[
                        filter_name
                    ]
                )

                column = definition["column"]
                operator_symbol = (
                    definition["operator"]
                )

            # ------------------------------------------------
            # COLUMN CHECK
            # ------------------------------------------------

            if column not in result.columns:

                raise KeyError(
                    f"Column '{column}' required "
                    f"for filter '{filter_name}' "
                    f"is not available."
                )

            # ------------------------------------------------
            # D/E SPECIAL CASE
            # ------------------------------------------------

            if filter_name == "de_max":

                mask = self._apply_de_filter(
                    result,
                    threshold,
                    operator_symbol
                )

            # ------------------------------------------------
            # ICR SPECIAL CASE
            # ------------------------------------------------

            elif filter_name == "icr_min":

                debt_free_mask = (
                    result["icr_label"]
                    .fillna("")
                    .astype(str)
                    .str.strip()
                    .str.lower()
                    .eq("debt free")
                )

                normal_values = pd.to_numeric(
                    result["interest_coverage"],
                    errors="coerce"
                )

                normal_mask = (
                    normal_values.notna()
                    &
                    self._apply_operator(
                        normal_values,
                        operator_symbol,
                        threshold
                    )
                )

                # Debt-free companies pass automatically
                mask = (
                    debt_free_mask
                    | normal_mask
                )

            # ------------------------------------------------
            # NORMAL FILTER
            # ------------------------------------------------

            else:

                values = pd.to_numeric(
                    result[column],
                    errors="coerce"
                )

                mask = (
                    values.notna()
                    &
                    self._apply_operator(
                        values,
                        operator_symbol,
                        threshold
                    )
                )

            result = result.loc[
                mask
            ]

        return result.reset_index(
            drop=True
        )

    # ========================================================
    # P10 / P90 WINSORIZATION
    # ========================================================

    @staticmethod
    def _winsorize(series):

        numeric = pd.to_numeric(
            series,
            errors="coerce"
        )

        valid = numeric.dropna()

        if valid.empty:
            return numeric

        p10 = valid.quantile(
            0.10
        )

        p90 = valid.quantile(
            0.90
        )

        return numeric.clip(
            lower=p10,
            upper=p90
        )

    # ========================================================
    # NORMALIZE HIGHER = BETTER
    # ========================================================

    @staticmethod
    def _normalize_positive(
        series
    ):

        numeric = pd.to_numeric(
            series,
            errors="coerce"
        )

        valid = numeric.dropna()

        output = pd.Series(
            50.0,
            index=series.index,
            dtype=float
        )

        if valid.empty:
            return output

        low = valid.min()
        high = valid.max()

        if high == low:
            output.loc[
                numeric.notna()
            ] = 50.0

            return output

        output.loc[
            numeric.notna()
        ] = (
            (
                numeric.loc[numeric.notna()]
                - low
            )
            /
            (high - low)
            * 100
        )

        return output

    # ========================================================
    # NORMALIZE LOWER = BETTER
    # ========================================================

    @staticmethod
    def _normalize_negative(
        series
    ):

        numeric = pd.to_numeric(
            series,
            errors="coerce"
        )

        valid = numeric.dropna()

        output = pd.Series(
            50.0,
            index=series.index,
            dtype=float
        )

        if valid.empty:
            return output

        low = valid.min()
        high = valid.max()

        if high == low:
            output.loc[
                numeric.notna()
            ] = 50.0

            return output

        output.loc[
            numeric.notna()
        ] = (
            (
                high
                - numeric.loc[numeric.notna()]
            )
            /
            (high - low)
            * 100
        )

        return output

    # ========================================================
    # SECTOR RELATIVE NORMALIZATION
    # ========================================================

    def _sector_normalize(
        self,
        df,
        column,
        higher_is_better=True
    ):

        output = pd.Series(
            50.0,
            index=df.index,
            dtype=float
        )

        if column not in df.columns:
            return output

        sectors = (
            df["broad_sector"]
            .fillna("Unknown")
        )

        for sector, indices in sectors.groupby(
            sectors
        ).groups.items():

            values = df.loc[
                indices,
                column
            ]

            winsorized = (
                self._winsorize(
                    values
                )
            )

            if higher_is_better:

                normalized = (
                    self._normalize_positive(
                        winsorized
                    )
                )

            else:

                normalized = (
                    self._normalize_negative(
                        winsorized
                    )
                )

            output.loc[
                indices
            ] = normalized

        return output

    # ========================================================
    # CFO / PAT RATIO
    # ========================================================

    @staticmethod
    def _calculate_cfo_pat(
        df
    ):

        cfo = pd.to_numeric(
            df["cash_from_operations_cr"],
            errors="coerce"
        )

        pat = pd.to_numeric(
            df["net_profit"],
            errors="coerce"
        )

        output = pd.Series(
            np.nan,
            index=df.index,
            dtype=float
        )

        valid = (
            cfo.notna()
            &
            pat.notna()
            &
            (pat != 0)
        )

        output.loc[valid] = (
            cfo.loc[valid]
            /
            pat.loc[valid]
        )

        return output

    # ========================================================
    # FCF POSITIVE
    # ========================================================

    @staticmethod
    def _calculate_fcf_positive(
        df
    ):

        fcf = pd.to_numeric(
            df["free_cash_flow"],
            errors="coerce"
        )

        return (
            fcf > 0
        ).astype(float) * 100

    # ========================================================
    # FCF CAGR
    # ========================================================

    def _calculate_fcf_cagr(
        self,
        df
    ):

        conn = self._connect()

        query = """
        SELECT
            company_id,
            year,
            free_cash_flow
        FROM financial_ratios
        ORDER BY company_id, year
        """

        history = pd.read_sql_query(
            query,
            conn
        )

        conn.close()

        output = pd.Series(
            np.nan,
            index=df.index,
            dtype=float
        )

        if history.empty:
            return output

        history = history.sort_values(
            ["company_id", "year"]
        )

        for idx, row in df.iterrows():

            company_id = row[
                "company_id"
            ]

            company_history = history[
                history["company_id"]
                == company_id
            ]

            if company_history.empty:
                continue

            latest = (
                company_history.iloc[-1]
            )

            target_year = (
                latest["year"] - 5
            )

            previous_rows = (
                company_history[
                    company_history["year"]
                    <= target_year
                ]
            )

            if previous_rows.empty:
                continue

            previous = (
                previous_rows.iloc[-1]
            )

            start = previous[
                "free_cash_flow"
            ]

            end = latest[
                "free_cash_flow"
            ]

            # CAGR is meaningful only
            # when both values are positive.
            if (
                pd.isna(start)
                or pd.isna(end)
                or start <= 0
                or end <= 0
            ):
                continue

            output.loc[idx] = (
                (
                    end / start
                ) ** (1 / 5)
                - 1
            ) * 100

        return output

    # ========================================================
    # COMPOSITE SCORE
    # ========================================================

    def calculate_composite_quality_score(
        self,
        df
    ):

        result = df.copy()

        if result.empty:

            result[
                "composite_quality_score"
            ] = pd.Series(
                dtype=float
            )

            return result

        # ----------------------------------------------------
        # SUPPORTING METRICS
        # ----------------------------------------------------

        result["cfo_pat_ratio"] = (
            self._calculate_cfo_pat(
                result
            )
        )

        result["fcf_positive"] = (
            pd.to_numeric(
                result["free_cash_flow"],
                errors="coerce"
            )
            > 0
        ).astype(int)

        result["fcf_cagr"] = (
            self._calculate_fcf_cagr(
                result
            )
        )

        # ----------------------------------------------------
        # PROFITABILITY — 35%
        #
        # ROE  = 15%
        # ROCE = 10%
        # NPM  = 10%
        # ----------------------------------------------------

        roe_score = (
            self._sector_normalize(
                result,
                "return_on_equity",
                True
            )
        )

        roce_score = (
            self._sector_normalize(
                result,
                "return_on_capital",
                True
            )
        )

        npm_score = (
            self._sector_normalize(
                result,
                "net_profit_margin",
                True
            )
        )

        profitability = (
            roe_score * 15 / 35
            +
            roce_score * 10 / 35
            +
            npm_score * 10 / 35
        )

        # ----------------------------------------------------
        # CASH QUALITY — 30%
        #
        # FCF CAGR       = 15%
        # CFO/PAT        = 10%
        # FCF Positive   = 5%
        # ----------------------------------------------------

        fcf_cagr_score = (
            self._sector_normalize(
                result,
                "fcf_cagr",
                True
            )
        )

        cfo_pat_score = (
            self._sector_normalize(
                result,
                "cfo_pat_ratio",
                True
            )
        )

        fcf_positive_score = (
            result["fcf_positive"]
            * 100
        )

        cash_quality = (
            fcf_cagr_score * 15 / 30
            +
            cfo_pat_score * 10 / 30
            +
            fcf_positive_score * 5 / 30
        )

        # ----------------------------------------------------
        # GROWTH — 20%
        #
        # Revenue CAGR = 10%
        # PAT CAGR     = 10%
        # ----------------------------------------------------

        revenue_growth_score = (
            self._sector_normalize(
                result,
                "revenue_cagr_5yr",
                True
            )
        )

        pat_growth_score = (
            self._sector_normalize(
                result,
                "pat_cagr_5yr",
                True
            )
        )

        growth = (
            revenue_growth_score * 10 / 20
            +
            pat_growth_score * 10 / 20
        )

        # ----------------------------------------------------
        # LEVERAGE — 15%
        #
        # D/E = 10%
        # ICR = 5%
        # ----------------------------------------------------

        de_score = (
            self._sector_normalize(
                result,
                "debt_to_equity",
                False
            )
        )

        icr_score = (
            self._sector_normalize(
                result,
                "interest_coverage",
                True
            )
        )

        # Debt-free companies receive
        # maximum ICR score.
        debt_free_mask = (
            result["icr_label"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.lower()
            .eq("debt free")
        )

        icr_score.loc[
            debt_free_mask
        ] = 100

        leverage = (
            de_score * 10 / 15
            +
            icr_score * 5 / 15
        )

        # ----------------------------------------------------
        # FINAL 0–100 SCORE
        # ----------------------------------------------------

        score = (
            profitability
            +
            cash_quality
            +
            growth
            +
            leverage
        )

        result[
            "composite_quality_score"
        ] = (
            score
            .clip(
                lower=0,
                upper=100
            )
            .round(2)
        )

        return result

    # ========================================================
    # SCREEN
    # ========================================================

    def screen(
        self,
        thresholds
    ):

        df = self.load_data()

        df = self.apply_filters(
            df,
            thresholds
        )

        df = (
            self.calculate_composite_quality_score(
                df
            )
        )

        df = df.sort_values(
            "composite_quality_score",
            ascending=False
        )

        return df.reset_index(
            drop=True
        )

    # ========================================================
    # RUN PRESET
    # ========================================================

    def run_preset(
        self,
        preset_name
    ):

        presets = self.config.get(
            "presets",
            {}
        )

        if preset_name not in presets:

            raise KeyError(
                f"Preset '{preset_name}' "
                f"not found.\n"
                f"Available presets: "
                f"{list(presets.keys())}"
            )

        thresholds = presets[
            preset_name
        ]

        return self.screen(
            thresholds
        )


# ============================================================
# MAIN TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("NIFTY 100 SCREENER ENGINE")
    print("=" * 60)

    try:

        engine = ScreenerEngine()

        print(
            "\nConfiguration loaded successfully."
        )

        print(
            "\nAvailable presets:"
        )

        for preset in engine.config[
            "presets"
        ]:

            print(
                f"  - {preset}"
            )

        print(
            "\nTesting database connection..."
        )

        data = engine.load_data()

        print(
            "Database loaded successfully."
        )

        print(
            "Companies available: "
            f"{data['company_id'].nunique()}"
        )

        print(
            "\nRunning all presets...\n"
        )

        results = {}

        for preset in engine.config[
            "presets"
        ]:

            try:

                result = (
                    engine.run_preset(
                        preset
                    )
                )

                results[preset] = result

                print(
                    f"{preset:<25} -> "
                    f"{len(result):>3} companies"
                )

            except Exception as exc:

                print(
                    f"{preset:<25} -> "
                    f"ERROR: {exc}"
                )

        print(
            "\n" + "=" * 60
        )

        print(
            "SCREENER ENGINE TEST COMPLETED"
        )

        print(
            "=" * 60
        )

    except Exception as exc:

        print(
            "\nERROR:"
        )

        print(exc)

        raise