import pandas as pd
import numpy as np
import statsmodels.api as sm
from sklearn.preprocessing import StandardScaler

# Load saved data
df = pd.read_csv('county_netmig_65plus_data.csv', dtype={'fips': str})
df['fips'] = df['fips'].astype(str).str.zfill(5)

# Regression setup - REMOVED pct_55_64_2010
feature_cols = ['pct_65plus_2010', 'log_pop_2010',
                'is_south', 'is_west', 'healthcare_share_2010',
                'manufacturing_share_2010', 'is_coastal', 'Scale',
                'median_hh_income_2010', 'median_house_value_2010',
                'state_income_tax_2010', 'is_rural', 'is_metro']
feature_cols = [c for c in feature_cols if c in df.columns]

BINARY_VARS = ['is_south', 'is_west', 'is_coastal', 'is_rural', 'is_metro']
VAR_MAP = {
    'pct_65plus_2010': 'Pop. 65+ Share',
    'log_pop_2010': 'Log Total Population',
    'is_rural': 'Bottom Quartile Pop. Density',
    'is_metro': 'Top Quartile Pop. Density',
    'is_south': 'Region: South',
    'is_west': 'Region: West',
    'is_coastal': 'Coastal County',
    'Scale': 'Natural Amenities Scale',
    'healthcare_share_2010': 'Healthcare Empl. Share',
    'manufacturing_share_2010': 'Manufacturing Empl. Share',
    'median_hh_income_2010': r'Median HH Income (\$000s)',
    'median_house_value_2010': r'Median House Value (\$0000s)',
    'state_income_tax_2010': 'State Income Tax Rate',
    'const': 'Intercept'
}
VAR_CATEGORIES = {
    'demographic': ['pct_65plus_2010', 'log_pop_2010', 'is_rural', 'is_metro'],
    'geographic': ['is_south', 'is_west', 'is_coastal', 'Scale'],
    'economic': ['healthcare_share_2010', 'manufacturing_share_2010', 'median_hh_income_2010',
                 'median_house_value_2010', 'state_income_tax_2010']
}

reg_df = df.dropna(subset=feature_cols + ['net_migration_rate_65plus', 'total_expected_65plus'])
X_raw = reg_df[feature_cols]
scaler = StandardScaler()
X_scaled = pd.DataFrame(scaler.fit_transform(X_raw), columns=X_raw.columns, index=X_raw.index)
X_sm = sm.add_constant(X_scaled)
y = reg_df['net_migration_rate_65plus']
weights = reg_df['total_expected_65plus']

# State FIPS for clustering
state_groups = reg_df['fips'].str[:2]

# Fit both models with state-clustered SEs
ols = sm.OLS(y, X_sm).fit(cov_type='cluster', cov_kwds={'groups': state_groups})
wls = sm.WLS(y, X_sm, weights=weights).fit(cov_type='cluster', cov_kwds={'groups': state_groups})

# Compute Partial R-squared for OLS
full_r2_ols = ols.rsquared
partial_r2_ols = {}
for var in feature_cols:
    reduced_cols = [c for c in feature_cols if c != var]
    X_reduced = sm.add_constant(X_scaled[reduced_cols])
    reduced_model = sm.OLS(y, X_reduced).fit()
    partial_r2_ols[var] = (full_r2_ols - reduced_model.rsquared) / (1 - reduced_model.rsquared) if reduced_model.rsquared < 1 else 0

# Compute Partial R-squared for WLS
full_r2_wls = wls.rsquared
partial_r2_wls = {}
for var in feature_cols:
    reduced_cols = [c for c in feature_cols if c != var]
    X_reduced = sm.add_constant(X_scaled[reduced_cols])
    reduced_model = sm.WLS(y, X_reduced, weights=weights).fit()
    partial_r2_wls[var] = (full_r2_wls - reduced_model.rsquared) / (1 - reduced_model.rsquared) if reduced_model.rsquared < 1 else 0

def format_coef(coef, pval):
    if pval < 0.01:
        return f"{coef:.3f}$^{{***}}$"
    elif pval < 0.05:
        return f"{coef:.3f}$^{{**}}$"
    elif pval < 0.1:
        return f"{coef:.3f}$^{{*}}$"
    return f"{coef:.3f}"

def get_var_label(var):
    base_name = VAR_MAP.get(var, var.replace('_', ' ').title())
    if var in BINARY_VARS:
        return base_name
    return f"{base_name} (z)"

# Generate LaTeX table - OLS and WLS with SE below, Partial R² for each
latex_str = r"""\begin{table}[htbp!]
\centering
\caption{Correlates of Senior Net Migration Rate (2010--2020)}
\label{tab:netmig_regression}
\begin{tabular}{lcccc}
\hline\hline
 & \multicolumn{4}{c}{\textit{Dependent Variable: Net Senior Migration Rate, 2010--2020}} \\
\cmidrule(lr){2-5}
 & \multicolumn{2}{c}{OLS} & \multicolumn{2}{c}{WLS} \\
\cmidrule(lr){2-3} \cmidrule(lr){4-5}
 & Coef. & Partial $R^2$ & Coef. & Partial $R^2$ \\
\hline
"""

category_labels = {
    'demographic': r'\textit{Demographic Variables}',
    'geographic': r'\textit{Geographic \& Climate Variables}',
    'economic': r'\textit{Economic Variables}'
}

for cat_key in ['demographic', 'geographic', 'economic']:
    cat_label = category_labels[cat_key]
    latex_str += f"{cat_label} & & & & \\\\\n"

    cat_vars = [v for v in VAR_CATEGORIES[cat_key] if v in ols.params.index]
    for var in cat_vars:
        var_label = get_var_label(var)
        ols_coef = format_coef(ols.params[var], ols.pvalues[var])
        ols_se = f"({ols.bse[var]:.3f})"
        ols_pr2 = partial_r2_ols[var]
        wls_coef = format_coef(wls.params[var], wls.pvalues[var])
        wls_se = f"({wls.bse[var]:.3f})"
        wls_pr2 = partial_r2_wls[var]
        # Coef row
        latex_str += f"\\quad {var_label} & {ols_coef} & {ols_pr2:.3f} & {wls_coef} & {wls_pr2:.3f} \\\\\n"
        # SE row
        latex_str += f" & {ols_se} & & {wls_se} & \\\\\n"
    latex_str += "[3pt]\n"

# Intercept
ols_coef = format_coef(ols.params['const'], ols.pvalues['const'])
ols_se = f"({ols.bse['const']:.3f})"
wls_coef = format_coef(wls.params['const'], wls.pvalues['const'])
wls_se = f"({wls.bse['const']:.3f})"
latex_str += f"Intercept & {ols_coef} & -- & {wls_coef} & -- \\\\\n"
latex_str += f" & {ols_se} & & {wls_se} & \\\\\n"

latex_str += "\\hline\n"
latex_str += f"Observations & {int(ols.nobs)} & & {int(wls.nobs)} & \\\\\n"
latex_str += f"$R^2$ & {ols.rsquared:.3f} & & {wls.rsquared:.3f} & \\\\\n"
latex_str += f"Dep. Var. Mean & {y.mean():.2f} & & {np.average(y, weights=weights):.2f} & \\\\\n"
latex_str += r"""\hline\hline
\multicolumn{5}{l}{\footnotesize $^{*}p<0.1$; $^{**}p<0.05$; $^{***}p<0.01$. (z) = standardized.} \\
\multicolumn{5}{l}{\footnotesize SEs clustered at state level. WLS weights by expected 65+ population.} \\
\multicolumn{5}{l}{\footnotesize Partial $R^2$ = share of unexplained variance explained by predictor.} \\
\multicolumn{5}{l}{\footnotesize Net migration data from Egan \& Robertson (2024).} \\
\end{tabular}
\end{table}"""

with open('figures/netmig_regression_table.tex', 'w') as f:
    f.write(latex_str)
print('Table regenerated - OLS & WLS with SE below, Partial R2 for each')
print(f'OLS: N = {int(ols.nobs)}, R2 = {ols.rsquared:.3f}')
print(f'WLS: N = {int(wls.nobs)}, R2 = {wls.rsquared:.3f}')
