# Intended validation: Run all six original Phase 4 validation sections.
# Preserve their mathematical fixtures, counterexamples, assumptions and findings.
# Detailed intended-validation comments precede each section below.
# A successful run means all implementation checks completed; it does not mean
# every manuscript claim is supported. Findings retain their original statuses.
# Title: Phase 4 forensic ledger and balance sheet validation
# Requires Python 3.9+; install dependencies: python -m pip install numpy scipy
# Run: python phase4_forensic_ledger_and_balance_sheet_validation.py
# Save JSON: python phase4_forensic_ledger_and_balance_sheet_validation.py --output phase4_results.json
# Standalone: no companion Python scripts or data files are required.


# MIT License
# Copyright (c) September 2026 Roger Cooperman; A.E. Petrunina V.V.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import argparse
from collections import Counter
import json
import platform
from pathlib import Path
import numpy as np
import scipy
from decimal import Decimal as D
import math
from fractions import Fraction as F

def require(condition, label):
    """Implementation self-check, not an assertion that the paper is correct."""
    if not condition:
        raise AssertionError(label)

def debt(events,rate,penalty):
    return sum((D(e['fmv'])-D(e['accepted_basis']))*rate*(1+penalty)*D(e['interest_factor']) for e in events)

def constant_value_case(n,rate,penalty):
    value=F(100)
    return value*n*rate*(1+penalty),value

# Original Phase 4 ledger fixture, embedded without changes.
TABLE_JSON = '{\n  "source_section": "4.2",\n  "headers": [\n    "Hop",\n    "Ledger CA",\n    "Ledger CB",\n    "Action & Asset Transition",\n    "Gross FMV ($)",\n    "Basis ($)",\n    "Base Gain ($)",\n    "Penalty & Interest ($)",\n    "Cumulative Debt ($)"\n  ],\n  "rows": [\n    {\n      "hop": 0,\n      "origin": "Off-Chain",\n      "destination": "Ethereum",\n      "action": "Initial Acquisition (Missing Records)",\n      "fmv": "15000000",\n      "basis": "0.00",\n      "base_gain": "0",\n      "penalty_interest": "0",\n      "cumulative_debt": "0"\n    },\n    {\n      "hop": 1,\n      "origin": "Ethereum",\n      "destination": "Ethereum",\n      "action": "DEX Swap: 5,000 ETH \\u219214.9M USDC",\n      "fmv": "14900000",\n      "basis": "0.00",\n      "base_gain": "14900000",\n      "penalty_interest": "2384000",\n      "cumulative_debt": "5364000"\n    },\n    {\n      "hop": 2,\n      "origin": "Ethereum",\n      "destination": "Arbitrum",\n      "action": "Bridge Lock: 14.9M USDC \\u2192Arbitrum",\n      "fmv": "14850000",\n      "basis": "0.00",\n      "base_gain": "14850000",\n      "penalty_interest": "2376000",\n      "cumulative_debt": "10710000"\n    },\n    {\n      "hop": 3,\n      "origin": "Arbitrum",\n      "destination": "Arbitrum",\n      "action": "Peeling Split: 10M USDC \\u2192wBTC",\n      "fmv": "10000000",\n      "basis": "0.00",\n      "base_gain": "10000000",\n      "penalty_interest": "1600000",\n      "cumulative_debt": "14310000"\n    },\n    {\n      "hop": 4,\n      "origin": "Arbitrum",\n      "destination": "Arbitrum",\n      "action": "Peeling Split: 4.8M USDC \\u2192wETH",\n      "fmv": "4800000",\n      "basis": "0.00",\n      "base_gain": "4800000",\n      "penalty_interest": "768000",\n      "cumulative_debt": "16038000"\n    },\n    {\n      "hop": 5,\n      "origin": "Arbitrum",\n      "destination": "Avalanche",\n      "action": "Bridge Burn/Mint: wBTC \\u2192AVAX",\n      "fmv": "9900000",\n      "basis": "0.00",\n      "base_gain": "9900000",\n      "penalty_interest": "1584000",\n      "cumulative_debt": "19602000"\n    },\n    {\n      "hop": 6,\n      "origin": "Arbitrum",\n      "destination": "Avalanche",\n      "action": "Bridge Burn/Mint: wETH \\u2192AVAX",\n      "fmv": "4750000",\n      "basis": "0.00",\n      "base_gain": "4750000",\n      "penalty_interest": "760000",\n      "cumulative_debt": "21312000"\n    },\n    {\n      "hop": 7,\n      "origin": "Avalanche",\n      "destination": "Off-Ramp",\n      "action": "VASP Consolidation & Liquidation",\n      "fmv": "14600000",\n      "basis": "0.00",\n      "base_gain": "14600000",\n      "penalty_interest": "2336000",\n      "cumulative_debt": "26568000"\n    }\n  ]\n}\n'

def load_table():
    """Return a fresh copy of the original ledger fixture."""
    return json.loads(TABLE_JSON)

# Intended validation: Section 4.2 and Theorem 4.3 numerical totals.
# Reproduce every table increment using exact decimal arithmetic; independently
# total gains, base tax, penalty, implied interest, debt and terminal deficit.
# Source rows from phase4_table.json are embedded below; no legal classification is inferred.

def validate_table_arithmetic():
    """Run this section with an independent findings list."""
    results = []

    def record(claim, status, explanation, **evidence):
        results.append(dict(claim=claim, status=status,
                            explanation=explanation, evidence=evidence))

    rows=load_table()['rows']
    cumulative=D(0);details=[]
    for row in rows:
        gain=D(row['base_gain']);base=gain*D('.20')
        extra=D(row['penalty_interest'])
        penalty=base*D('.75');implied_interest=extra-penalty
        previous=cumulative;cumulative+=base+extra
        require(cumulative==D(row['cumulative_debt']),'cumulative row '+str(row['hop']))
        require(gain==D(row['fmv']) if row['hop'] else gain==0,'source gain row')
        details.append(dict(hop=row['hop'],base_tax=str(base),penalty=str(penalty),
                            implied_interest=str(implied_interest),increment=str(cumulative-previous)))
    gains=sum(D(r['base_gain']) for r in rows)
    base=gains*D('.20');penalty=base*D('.75')
    extra=sum(D(r['penalty_interest']) for r in rows)
    interest=extra-penalty
    require(gains==D(73800000) and base==D(14760000),'gains and tax')
    require(penalty==D(11070000) and interest==D(738000),'penalty and interest')
    require(cumulative==D(26568000),'total debt')
    deficit=D(rows[-1]['fmv'])-cumulative
    require(deficit==D(-11968000),'published deficit')
    record('4.2–4.3 published arithmetic','supported under stated assumptions',
           'All row increments and headline totals reproduce exactly when the supplied gain and extra-charge columns are taken as inputs.',
           row_checks=details,total_gains=str(gains),base_tax=str(base),penalty=str(penalty),
           implied_interest=str(interest),total_debt=str(cumulative),terminal_liquidity_minus_debt=str(deficit))
    require(D(rows[0]['fmv'])>0 and D(rows[0]['base_gain'])==0,'initial acquisition exception')
    record('4.2 event inclusion','insufficiently specified',
           'Hop 0 has zero basis and positive FMV but zero gain. An event-classification rule, rather than zero basis alone, determines which rows enter the sum. The remaining taxable-event labels are supplied premises.')
    return results


# Intended validation: Proposition 4.1, Definition 4.1.2 and Section 4.2.
# Infer the interest convention in the table and compare it with the stated
# exponential formula, both with common one-year and illustrative staggered
# accrual periods. Missing dates prevent unique statutory reconciliation.

def validate_interest_reconciliation():
    """Run this section with an independent findings list."""
    results = []

    def record(claim, status, explanation, **evidence):
        results.append(dict(claim=claim, status=status,
                            explanation=explanation, evidence=evidence))

    rows=load_table()['rows'][1:]
    details=[];paper_total=0.;table_total=D(0)
    for row in rows:
        base=D(row['base_gain'])*D('.20')
        penalty=base*D('.75')
        interest=D(row['penalty_interest'])-penalty
        require(interest==base*D('.05'),'implied simple interest')
        table=base+penalty+interest
        continuous=float(base)*1.75*math.exp(.05)
        details.append(dict(hop=row['hop'],table_debt=str(table),
                            one_year_formula_debt=continuous,difference=continuous-float(table)))
        table_total+=table;paper_total+=continuous
    base_total=sum(D(r['base_gain'])*D('.20') for r in rows)
    simple_on_tax=base_total*(D(1)+D('.75')+D('.05'))
    simple_on_penalized=base_total*D('1.75')*D('1.05')
    require(simple_on_tax==table_total,'simple convention total')
    require(paper_total>float(table_total),'exponential mismatch')
    implied_years=math.log(1.8/1.75)/.05
    record('4.2 interest convention','supported under stated assumptions',
           'Every row contains a 75% penalty plus 5% of base tax as interest. Thus the table exactly uses base_tax*(1+.75+.05), which equals one year of simple interest on base tax only.',
           rows=details,table_total=str(table_total),simple_on_penalized_principal=str(simple_on_penalized),
           one_year_exponential_total=paper_total,one_year_exponential_difference=paper_total-float(table_total))
    record('4.1 formula versus 4.2 table','insufficiently specified',
           'The stated base_tax*1.75*exp(.05*age) does not reproduce the table at age=one year. It reproduces each row only at the same implied age of about .5634 years. Since actual accrual dates are absent, no unique exponential reconciliation is established.',
           common_implied_age_years=implied_years)
    # An illustrative schedule only, not recovered transaction dates.
    ages=[1.,5/6,4/6,3/6,2/6,1/6,0.]
    staggered=sum(float(D(r['base_gain'])*D('.20'))*1.75*math.exp(.05*t)
                  for r,t in zip(rows,ages))
    no_interest=float(base_total)*1.75
    require(no_interest<=staggered<=paper_total,'age bounds')
    record('4.1.2 date sensitivity','insufficiently specified',
           'A twelve-month routing window does not supply an accrual start date for every liability. If modeled ages lie in [0,1], exponential totals lie between the no-interest and all-one-year totals; the example schedule is synthetic.',
           assumed_ages=ages,illustrative_staggered_total=staggered,
           exponential_lower_bound=no_interest,exponential_upper_bound=paper_total)
    return results


# Intended validation: Section 4.2 routing and balance conservation.
# Reconstruct the implied split-and-merge fiat-valued flow; distinguish
# branch values from whole-portfolio values and sum unexplained reductions.
# Constant-value comparisons are bookkeeping assumptions, not token-level
# proofs of fees, prices, transaction ancestry, or cross-chain conservation.

def validate_branch_flow_accounting():
    """Run this section with an independent findings list."""
    results = []

    def record(claim, status, explanation, **evidence):
        results.append(dict(claim=claim, status=status,
                            explanation=explanation, evidence=evidence))

    rows=load_table()['rows'];v={r['hop']:D(r['fmv']) for r in rows}
    reductions=[v[0]-v[1],v[1]-v[2],v[2]-v[3]-v[4],
                v[3]-v[5],v[4]-v[6],v[5]+v[6]-v[7]]
    require(all(x>=0 for x in reductions),'nonnegative implied reductions')
    require(sum(reductions)==v[0]-v[7]==D(400000),'aggregate residual')
    record('4.2 split and merge reconciliation','supported under stated assumptions',
           'The implied topology 0->1->2, split into 3/4, then 3->5 and 4->6, followed by 5/6->7 reconciles to a 400000 reduction in fiat-valued capital.',
           stages=['0 to 1','1 to 2','2 to 3+4','3 to 5','4 to 6','5+6 to 7'],
           unexplained_reductions=[str(x) for x in reductions],total_reduction=str(sum(reductions)),
           fraction_of_initial=float(sum(reductions)/v[0]))
    require(v[5]>v[4],'sequential row value increase')
    record('4.2 rows versus path depth','insufficiently specified',
           'Rows 3/4 and 5/6 belong to different branches. Row 5 being larger than row 4 is not new capital. Seven listed events are not seven successive full-principal transformations on a single path.',
           listed_events=7,modeled_branch_paths=[[1,2,3,5,7],[1,2,4,6,7]],
           longest_listed_event_path=5)
    record('4.2 empirical support','insufficiently specified',
           'The table contains no transaction hashes, timestamps, per-asset quantities after acquisition, price sources, execution fees or explicit edge IDs. The split topology is inferred from labels. Residual fiat value cannot be attributed uniquely to fees rather than prices or omitted movements.')
    return results


# Intended validation: Definitions 4.1.1–4.1.2.
# Compare the declared nine-column simulation schema with the actual table;
# check the debt reduction with zero basis and its basis-sensitive general
# form. Test timestamp requirements and duplicated-event inflation.

def validate_ledger_schema_and_operator():
    """Run this section with an independent findings list."""
    results = []

    def record(claim, status, explanation, **evidence):
        results.append(dict(claim=claim, status=status,
                            explanation=explanation, evidence=evidence))

    source=load_table();rows=source['rows'][1:]
    events=[dict(fmv=r['fmv'],accepted_basis='0',interest_factor='1') for r in rows]
    result=debt(events,D('.20'),D('.75'))
    require(result==D(25830000),'zero-basis operator before interest')
    record('4.1.2 cumulative operator','supported under stated assumptions',
           'With explicitly supplied accepted bases, rates and interest factors, the event sum gives 25830000 before interest. Using the table-specific factor 1.80/1.75 would reconcile its debt total, but is not an independently established accrual rule.',
           pre_interest_total=str(result))
    alternative=[dict(fmv='100',accepted_basis='80',interest_factor='1')]
    require(debt(alternative,D('.20'),D('.75'))==7,'basis-sensitive operator')
    record('4.1.2 zero-basis premise','insufficiently specified',
           'The operator depends on the accepted-basis input. Zero basis is assumed here and is not inferred from the row data. A 100 disposition with accepted basis 80 yields 7 under the same rate and penalty model.',
           alternative_model_debt='7')
    record('4.1.1 schema mismatch','contradicted',
           'The declared columns include separate consumed/emitted assets, claimed basis, base tax and punitive debt added. The actual table instead combines action/assets and includes base gain, penalty-and-interest, and cumulative debt. Equal column counts do not make them the same schema.',
           declared_columns=['Hop','Origin Ledger','Destination Ledger','Consumed Asset','Emitted Asset','FMV','Claimed Basis','Base Tax','Punitive Debt Added'],
           actual_columns=source['headers'])
    require(any(isinstance(r['origin'],str) for r in rows),'categorical fields')
    record('4.1.1 real matrix representation','insufficiently specified',
           'Chain and asset labels are categorical strings, so the unencoded table is not an element of R^(N x 9). A typed record schema or explicit categorical encoding is required. The age t_now-t_k also needs timestamps absent from both the declared columns and the actual table.')
    doubled=debt(events+[events[0]],D('.20'),D('.75'))
    inflation=D(rows[0]['base_gain'])*D('.20')*D('1.75')
    require(doubled-result==inflation,'duplicate inflation')
    record('4.1.2 unique event identifiers','insufficiently specified',
           'The sum counts each supplied row once. Duplicate ingestion increases debt unless unique disposition identifiers and event rules are enforced.',
           duplicate_first_event_inflation=str(inflation))
    return results


# Intended validation: Proposition 4.1 and its N>=10 assertion.
# Test the assertion under explicit rate/fee/value assumptions; distinguish
# event count from depth, finite geometric growth from exponential growth,
# and the earliest crossing in the supplied cumulative-debt table.

def validate_hop_threshold_and_growth():
    """Run this section with an independent findings list."""
    results = []

    def record(claim, status, explanation, **evidence):
        results.append(dict(claim=claim, status=status,
                            explanation=explanation, evidence=evidence))

    debt,terminal=constant_value_case(10,F(1,5),F(3,4))
    require(debt==350 and debt>terminal,'fixed-rate ten event case')
    record('4.1 ten events under fixed inputs','supported under stated assumptions',
           'At 20% tax, 75% penalty, no interest, zero basis and ten equally valued full-principal dispositions, debt is 3.5 times terminal value. These explicit assumptions are sufficient for this example.',
           debt=str(debt),terminal_value=str(terminal))
    debt,terminal=constant_value_case(10,F(1,100),F(3,4))
    require(debt<terminal,'rate dependence')
    record('4.1 universal ten-event threshold','insufficiently specified',
           'Zero basis and event count alone do not imply debt exceeds terminal value. At a modeled 1% rate the same ten-event construction gives debt 17.5 against terminal value 100. This changes the numerical 20% scenario, so it tests the unqualified proposition, not that scenario.',
           debt=str(debt),terminal_value=str(terminal))
    # Ten small dispositions plus a terminal unconverted holding are compatible
    # with a multi-branch graph, unlike a repeated full-principal chain.
    small_debt=F(10)*F(1)*F(1,5)*F(7,4)
    require(small_debt==F(7,2) and small_debt<100,'small disposition counterexample')
    record('4.1 graph scope at stated rates','insufficiently specified',
           'At the stated 20%/75% rates, ten dispositions each worth 1 produce debt 3.5; a separate retained holding of 100 remains larger. To rule this out, the proposition must require how much capital each counted event traverses.',
           total_modeled_debt=str(small_debt),retained_holding='100')
    q=F(99,100);rate=F(1,5);penalty=F(3,4);v0=F(100)
    limit=rate*(1+penalty)*v0*q/(1-q)
    d10=rate*(1+penalty)*sum(v0*q**k for k in range(1,11))
    require(d10<limit,'geometric bound')
    record('4.1 exponential accumulation','contradicted',
           'With constant principal per event and fixed accrual factors, debt grows linearly in event count. With a positive constant fee and declining value it is a bounded geometric sum. Exponential growth in elapsed time under an interest model is distinct from growth in hop count.',
           fee_model_debt_at_10=float(d10),fee_model_asymptotic_limit=float(limit))
    rows=load_table()['rows'][1:]
    # Interpret residuals from the branch-flow script as real losses, with
    # no independent market appreciation or external assets.
    portfolio=[14900000,14850000,14850000,14800000,14700000,14650000,14600000]
    crossings=[r['hop'] for r,w in zip(rows,portfolio) if int(r['cumulative_debt'])>w]
    require(crossings[0]==4,'table portfolio crossing')
    record('4.2 observed example crossing','supported under stated assumptions',
           'Under the inferred branch bookkeeping and no other assets, cumulative debt first exceeds remaining portfolio value at row 4. The table has seven events and does not empirically test the N>=10 threshold.',
           inferred_portfolio_by_row=portfolio,first_crossing_row=crossings[0])
    return results


# Intended validation: Theorem 4.3.
# Reproduce the final deficit and distinguish liquidity coverage from total
# net worth. Test added assets and liabilities, the meaning of a deficit
# exceeding asset value, and whether mathematical totals establish authority.

def validate_balance_sheet_scope():
    """Run this section with an independent findings list."""
    results = []

    def record(claim, status, explanation, **evidence):
        results.append(dict(claim=claim, status=status,
                            explanation=explanation, evidence=evidence))

    row=load_table()['rows'][-1]
    liquidity,debt=D(row['fmv']),D(row['cumulative_debt'])
    net=liquidity-debt
    require(net==D(-11968000),'deficit')
    record('4.3 terminal deficit','supported under stated assumptions',
           'The provided terminal liquidity minus modeled debt is exactly -11968000.',
           liquidity=str(liquidity),debt=str(debt),difference=str(net),
           debt_to_liquidity_ratio=str(debt/liquidity))
    require(abs(net)<liquidity,'deficit magnitude comparison')
    record('4.3 deficit eclipses remaining asset value','contradicted',
           'If the theorem means the magnitude of the deficit exceeds asset value, its own figures contradict that wording: 11968000 is smaller than 14600000. Debt, rather than the deficit magnitude, exceeds terminal liquidity.',
           deficit_magnitude=str(abs(net)),terminal_asset_value=str(liquidity))
    offchain=D(20000000);other_liabilities=D(1000000)
    total=liquidity+offchain-debt-other_liabilities
    require(total==D(7032000) and total>0,'positive total net worth counterexample')
    record('4.3 global net worth inference','insufficiently specified',
           'The table demonstrates a shortfall against the routed liquidity only. With additional assets 20000000 and other liabilities 1000000, total modeled net worth is positive 7032000. Global insolvency requires a complete balance sheet.',
           additional_assets=str(offchain),other_liabilities=str(other_liabilities),total_net_worth=str(total))
    break_even=debt-liquidity
    require(liquidity+break_even-debt==0,'break-even assets')
    record('4.3 off-chain break-even amount','supported under stated assumptions',
           'With no other liabilities and using the published debt, additional assets of 11968000 bring total modeled net worth to zero.',
           additional_assets_required=str(break_even))
    record('4.3 legal and recovery conclusion','insufficiently specified',
           'The arithmetic does not establish taxable-event classifications, legally accepted basis, fraud, applicable interest, assessment authority, recoverability, or initiation of proceedings. These are unverified external premises.')
    return results


VALIDATORS = (
    ('01_table_arithmetic', validate_table_arithmetic),
    ('02_interest_reconciliation', validate_interest_reconciliation),
    ('03_branch_flow_accounting', validate_branch_flow_accounting),
    ('04_ledger_schema_and_operator', validate_ledger_schema_and_operator),
    ('05_hop_threshold_and_growth', validate_hop_threshold_and_growth),
    ('06_balance_sheet_scope', validate_balance_sheet_scope),
)

def run_all():
    """Run every section and return one structured report; safe to call again."""
    sections = [dict(section=name, results=validate()) for name, validate in VALIDATORS]
    counts = Counter(item['status'] for section in sections for item in section['results'])
    return dict(title='Phase 4 forensic ledger and balance sheet validation', script=Path(__file__).name,
                environment=dict(python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__),
                scope="Mathematical fixtures only; no real identity or legal findings.",
                summary=dict(sections=len(sections), findings=sum(counts.values()),
                             status_counts=dict(counts)), sections=sections)


def main():
    parser = argparse.ArgumentParser(description='Phase 4 forensic ledger and balance sheet validation')
    parser.add_argument('--output', type=Path, help='Also save the JSON report to this path.')
    args = parser.parse_args()
    report = json.dumps(run_all(), indent=2, allow_nan=False)
    if args.output is not None:
        args.output.write_text(report + '\n', encoding='utf-8')
    print(report)


if __name__ == '__main__':
    main()
