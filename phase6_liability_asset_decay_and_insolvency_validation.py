# Intended validation: phase6 liability asset decay and insolvency validation.
# Run all original phase checks and emit one JSON report.
# Successful execution confirms checks ran, not that all source claims hold.
# Usage: python phase6_liability_asset_decay_and_insolvency_validation.py --output phase6_results.json
# Dependencies: Python standard library only.

# MIT License
# Copyright (c) September 2026 Roger Cooperman; A.E. Petrunina V.V.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import json
import platform
from pathlib import Path

RESULTS = []

def require(condition, label):
    if not condition:
        raise AssertionError(label)

def record(claim, status, explanation, **evidence):
    RESULTS.append(dict(claim=claim, status=status, explanation=explanation, evidence=evidence))

# Source simulation inputs embedded so no companion data file is needed.
INPUTS = {'source': 'Phase 6 Theorem 6.1; event rows reused from Phase 4 section 4.2', 'phase6': {'initial': '15000000', 'terminal': '14600000', 'approximate_friction': '.026', 'gains': '73800000', 'base_tax': '14760000', 'penalized_tax': '25830000', 'demand': '26568000', 'deficit': '-11968000'}, 'phase4_events': [{'hop': 1, 'origin': 'Ethereum', 'destination': 'Ethereum', 'action': 'DEX Swap: 5,000 ETH →14.9M USDC', 'fmv': '14900000', 'cumulative_debt': '5364000'}, {'hop': 2, 'origin': 'Ethereum', 'destination': 'Arbitrum', 'action': 'Bridge Lock: 14.9M USDC →Arbitrum', 'fmv': '14850000', 'cumulative_debt': '10710000'}, {'hop': 3, 'origin': 'Arbitrum', 'destination': 'Arbitrum', 'action': 'Peeling Split: 10M USDC →wBTC', 'fmv': '10000000', 'cumulative_debt': '14310000'}, {'hop': 4, 'origin': 'Arbitrum', 'destination': 'Arbitrum', 'action': 'Peeling Split: 4.8M USDC →wETH', 'fmv': '4800000', 'cumulative_debt': '16038000'}, {'hop': 5, 'origin': 'Arbitrum', 'destination': 'Avalanche', 'action': 'Bridge Burn/Mint: wBTC →AVAX', 'fmv': '9900000', 'cumulative_debt': '19602000'}, {'hop': 6, 'origin': 'Arbitrum', 'destination': 'Avalanche', 'action': 'Bridge Burn/Mint: wETH →AVAX', 'fmv': '4750000', 'cumulative_debt': '21312000'}, {'hop': 7, 'origin': 'Avalanche', 'destination': 'Off-Ramp', 'action': 'VASP Consolidation & Liquidation', 'fmv': '14600000', 'cumulative_debt': '26568000'}]}

def load_inputs():
    return INPUTS


# Intended validation: Theorem 6.1 monetary identities and source lineage.
# Recompute gains from the Phase 4 event values reused by Phase 6, then
# verify base tax, penalized principal, implied interest and the final deficit
# using Decimal arithmetic. Repeated figures are not independent observations.

from decimal import Decimal as D

def validate_ledger_reconciliation():
    data=load_inputs()
    gains=sum(D(r['fmv']) for r in data['phase4_events'])
    stated=data['phase6']
    base=gains*D('.20');punitive=base*D('1.75')
    debt=D(stated['demand']);terminal=D(stated['terminal'])
    require(gains==D(stated['gains']),'gains total')
    require(base==D(stated['base_tax']),'base tax')
    require(punitive==D(stated['penalized_tax']),'penalized tax')
    require(terminal-debt==D(stated['deficit']),'deficit')
    record('6.1 published totals','supported under stated assumptions',
           'The seven earlier event FMVs sum to 73800000. The rate and penalty identities and stated terminal subtraction reproduce exactly.',
           gains=str(gains),base_tax=str(base),penalized_tax=str(punitive),
           implied_interest=str(debt-punitive),demand=str(debt),deficit=str(terminal-debt))
    previous=data['phase4_events'][-1]
    require(D(previous['cumulative_debt'])==debt and D(previous['fmv'])==terminal,'phase-to-phase values')
    record('6.1 empirical independence','insufficiently specified',
           'Phase 6 reuses the Phase 4 totals without providing a new ledger matrix or transaction observations. Reproducing them confirms arithmetic, not independent empirical validation.',
           source_event_count=len(data['phase4_events']))



# Intended validation: Theorem 6.1 decay recurrence and cumulative friction.
# Test exact product accounting, fee boundaries, the reported approximate
# friction, additive versus sequential charges, and the branch/path issue.
# Hypothetical percentages are model inputs, not measured protocol fees.

from decimal import Decimal as D
from fractions import Fraction as F
import math

def decay(value,amm,gas):
    if value<0 or amm<0 or gas<0 or amm+gas>1:
        raise ValueError('Require nonnegative value and fees with sum <=1')
    return value*(1-amm-gas)

def validate_asset_decay():
    d=load_inputs()['phase6'];initial=D(d['initial']);terminal=D(d['terminal'])
    exact=(initial-terminal)/initial
    approximate=initial*(1-D(d['approximate_friction']))
    require(initial-terminal==D(400000),'absolute capital change')
    require(approximate==D(14610000),'stated approximate rate')
    record('6.1 cumulative friction','insufficiently specified',
           'The exact implied reduction is 2.666666...%. Using .026 exactly gives 14610000, which is 10000 above the stated terminal value. The approximation needs a stated tolerance; this alone is not proof of an arithmetic contradiction.',
           exact_fraction='2/75',exact_rate=str(exact),stated_rate=d['approximate_friction'],
           implied_terminal_at_stated_rate=str(approximate),difference=str(approximate-terminal))
    fees=[(F(1,100),F(1,1000)),(F(1,200),F(1,1000)),(F(0),F(1,1000))]
    value=F(100);product=F(1)
    for amm,gas in fees:
        value=decay(value,amm,gas);product*=1-amm-gas
    require(value==100*product,'recurrence product identity')
    require(decay(F(100),F(0),F(0))==100 and decay(F(100),F(1),F(0))==0,'fee boundaries')
    try:decay(F(100),F(4,5),F(1,2))
    except ValueError:pass
    else:raise AssertionError('negative resulting balance')
    record('6.1 recurrence algebra','supported under stated assumptions',
           'For fees defined as fractions of the same incoming value, each step multiplies by 1-amm-gas. Cumulative friction is one minus the product of these factors; admissible fees must sum to at most one.',
           synthetic_terminal=str(value),synthetic_cumulative_friction=str(1-product))
    additive=decay(F(100),F(1,10),F(1,10))
    sequential=F(100)*F(9,10)*F(9,10)
    require(additive==80 and sequential==81,'charging bases differ')
    record('6.1 fee semantics and units','insufficiently specified',
           'Additive fractions assume a common charging base. Sequential 10% charges give 81 from 100, whereas subtracting both from the initial amount gives 80. Fixed gas amounts, AMM reserve-dependent output and cross-asset units need explicit conversion rules.',
           common_base_result=str(additive),sequential_result=str(sequential))
    values=[D(r['fmv']) for r in load_inputs()['phase4_events']]
    require(values[4]>values[3],'branch row increase')
    fitted=1-math.pow(float(terminal/initial),1/7)
    record('6.1 sequential versus branched ledger','insufficiently specified',
           'The reused table branches: the 4.8M row is followed by a 9.9M row on another branch. These are not sequential whole-portfolio values under nonnegative friction. A seven-step uniform fee can fit the endpoints, but that fit does not verify the actual routing.',
           preceding_branch_value=str(values[3]),following_branch_value=str(values[4]),
           illustrative_fitted_seven_step_fee=fitted)



# Intended validation: Theorem 6.1 compounding-interest total.
# Reconcile the implied interest with simple and exponential conventions,
# then vary synthetic accrual ages. Dates and statutory conventions are
# missing inputs; the script does not determine what any law requires.

from decimal import Decimal as D
import math

def validate_interest_model():
    d=load_inputs()['phase6'];base=D(d['base_tax']);penalized=D(d['penalized_tax']);demand=D(d['demand'])
    interest=demand-penalized
    require(interest==D(738000) and interest==base*D('.05'),'implied interest')
    record('6.1 implied interest arithmetic','supported under stated assumptions',
           'The stated demand implies interest of 738000, exactly 5% of base tax; it reconciles with one year of simple interest on base tax only.',
           implied_interest=str(interest),fraction_of_base=str(interest/base),fraction_of_penalized=str(interest/penalized))
    annual=.05
    compounded=float(penalized)*math.exp(annual)
    simple_penalized=penalized*D('1.05')
    implied_age=math.log(float(demand/penalized))/annual
    require(compounded>float(demand),'one-year exponential mismatch')
    record('6.1 stated compounding description','insufficiently specified',
           'Using the earlier 5% exponential model for one year on penalized tax gives a different demand. The stated amount can be fitted using another age or convention; actual start dates and treatment of penalties are not supplied.',
           one_year_continuous_total=compounded,difference_from_stated=compounded-float(demand),
           one_year_simple_on_penalized=str(simple_penalized),common_age_fitting_stated_total=implied_age)
    events=load_inputs()['phase4_events'];ages=[1,5/6,4/6,.5,2/6,1/6,0]
    staggered=sum(float(D(r['fmv'])*D('.35'))*math.exp(annual*t) for r,t in zip(events,ages))
    require(float(penalized)<=staggered<=compounded,'bounded modeled ages')
    record('6.1 accrual timeline','insufficiently specified',
           'A period containing several events does not assign an age to each assessed amount. This illustrative staggered calculation lies within the zero-to-one-year bounds; it is not a reconstruction of actual dates.',
           synthetic_ages=ages,synthetic_total=staggered,zero_age_total=str(penalized),one_year_upper_total=compounded)



# Intended validation: Theorem 6.1 claim that accumulated liability
# geometrically eclipses decaying assets. Separate absolute liability growth
# from the liability/remaining-asset ratio; derive a conditional crossing and
# test off-chain wealth and zero-rate countermodels without importing law.

from fractions import Fraction as F

def validate_growth_and_crossing():
    v0=F(100);q=F(99,100);m=F(7,20)
    ceiling=m*v0*q/(1-q)
    rows=[]
    for n in [1,3,10,100]:
        direct=m*sum((v0*q**k for k in range(1,n+1)),F(0))
        closed=ceiling*(1-q**n);assets=v0*q**n
        ratio=m*q/(1-q)*(q**(-n)-1)
        require(direct==closed and direct/assets==ratio,'sum and ratio identities')
        rows.append(dict(depth=n,liability=float(direct),remaining_assets=float(assets),ratio=float(ratio)))
    record('6.1 geometric comparison','supported under stated assumptions',
           'With constant q in (0,1), zero basis, positive fixed multiplier m and only the decaying principal as assets, debt approaches a finite ceiling while debt/remaining_assets grows as a constant times (q^(-N)-1). Geometric growth can describe the ratio, not unbounded absolute debt.',
           liability_ceiling=float(ceiling),examples=rows)
    first=next(n for n in range(1,100) if ceiling*(1-q**n)>v0*q**n)
    require(first==3,'first crossing fixture')
    record('6.1 conditional crossing','supported under stated assumptions',
           'For the synthetic m=.35 and q=.99 case without other assets, the first crossing is at N=3. A positive multiplier and enough full-principal events are essential conditions.',first_integer_crossing=first)
    offchain=F(4000)
    require(ceiling==3465 and ceiling<offchain,'offchain countermodel')
    record('6.1 total-entity insolvency guarantee','contradicted',
           'The recurrence alone does not guarantee total-entity insolvency. An admissible model with V0=100, q=.99, m=.35 and off-chain wealth 4000 has debt always below 3465, hence below off-chain assets alone.',
           liability_ceiling=str(ceiling),offchain_assets=str(offchain))
    record('6.1 zero basis alone','insufficiently specified',
           'Zero basis does not specify the tax rate, penalty eligibility, event values, event count or other wealth. If the multiplier is zero, debt is zero regardless of basis. This boundary example changes the document\'s stated positive numerical rate; it tests whether zero basis alone suffices.')



# Intended validation: Theorem 6.1 final deficit, net worth and forfeiture
# inference. Compare the published liquidity shortfall with complete balance
# sheet countermodels and a recoverability cap; no real enforcement or legal
# classification is performed.

from decimal import Decimal as D

def validate_deficit_and_recovery_scope():
    d=load_inputs()['phase6'];liquid=D(d['terminal']);debt=D(d['demand'])
    deficit=liquid-debt
    require(deficit==D(-11968000),'source deficit')
    record('6.1 deficit identity','supported under stated assumptions',
           'The published modeled debt exceeds the terminal routed liquidity by 11968000.',
           liquidity=str(liquid),debt=str(debt),liquidity_minus_debt=str(deficit))
    other_assets=D(20000000);other_debts=D(1000000)
    net=liquid+other_assets-debt-other_debts
    require(net==D(7032000) and net>0,'complete balance countermodel')
    record('6.1 negative global net worth','insufficiently specified',
           'The source supplies routed liquidity rather than a complete global balance sheet. With hypothetical additional assets 20000000 and other debts 1000000, modeled total net worth is positive 7032000.',
           additional_assets=str(other_assets),other_liabilities=str(other_debts),net_worth=str(net))
    accessible=liquid*D('.60');recovery=min(debt,accessible)
    require(debt>liquid and recovery<liquid,'recovery gap')
    record('6.1 certain total forfeiture','contradicted',
           'Debt greater than asset value does not mathematically imply every asset is recoverable. In a synthetic model with only 60% accessible, recovery is bounded by 8760000 despite the stated larger debt.',
           accessible_fraction='.60',maximum_model_recovery=str(recovery))
    record('6.1 legal consequences','insufficiently specified',
           'A ledger commitment or arithmetic sum does not specify taxable dispositions, accepted basis, fraud eligibility, statutory interest, authorization, or a duty to act immediately. These remain unverified external premises; no legal conclusions are supplied.')



# Run all validations; assertions signal failed checks, not contradicted claims.
def main():
    import argparse
    from collections import Counter
    parser = argparse.ArgumentParser(description='phase6 liability asset decay and insolvency validation')
    parser.add_argument("--output", type=Path, help="Also save the JSON report to this path.")
    args = parser.parse_args()
    RESULTS.clear()
    validate_ledger_reconciliation()
    validate_asset_decay()
    validate_interest_model()
    validate_growth_and_crossing()
    validate_deficit_and_recovery_scope()
    report = dict(phase=6, python=platform.python_version(), scope="Synthetic mathematical validation; no legal findings.", conclusion="Phase 6 is not validated as a whole.", assessment_counts=dict(Counter(item["status"] for item in RESULTS)), results=RESULTS)
    payload = json.dumps(report, indent=2, allow_nan=False)
    if args.output:
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
