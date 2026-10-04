# Intended validation: phase8 fifo twap and amm valuation validation.
# Run all original phase checks and emit one JSON report.
# Successful execution confirms checks ran, not that all source claims hold.
# Usage: python phase8_fifo_twap_and_amm_valuation_validation.py --output phase8_results.json
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


# Intended validation: Lemma 8.1 wallet-local lot vectors and provenance loss.
# Verify quantity, basis and acquisition-date preservation in a synthetic
# partial transfer; distinguish missing transmitted metadata, unknown basis
# and numeric zero. This is an accounting model, not a tax-law conclusion.

from fractions import Fraction as F

def validate_lot_transfer():
    lot=dict(id='lot_A',quantity=F(10),basis=F(1000),acquired='2020-01-01')
    amount=F(4);allocated=lot['basis']*amount/lot['quantity']
    sent=dict(id=lot['id'],quantity=amount,basis=allocated,acquired=lot['acquired'])
    kept=dict(id=lot['id'],quantity=lot['quantity']-amount,basis=lot['basis']-allocated,acquired=lot['acquired'])
    require(sent['quantity']+kept['quantity']==lot['quantity'],'quantity preservation')
    require(sent['basis']+kept['basis']==lot['basis'],'basis preservation')
    require(sent['acquired']==kept['acquired']==lot['acquired'],'acquisition date')
    record('8.1 transfer-state arithmetic','supported under stated assumptions',
           'A proportional partial-transfer model preserves total quantity, basis and acquisition date across separate wallet records.',
           sent_quantity=str(amount),sent_basis=str(allocated),remaining_basis=str(kept['basis']))
    wire=dict(reference='transfer_1',quantity=amount)
    records={'transfer_1':sent}
    restored=records[wire['reference']]
    require(restored['basis']==400,'external record reconstruction')
    record('8.1 identification probability equals zero','contradicted',
           'Missing metadata on the transfer itself does not logically imply unavailable provenance. A synthetic external record keyed by transfer reference recovers basis and date exactly. No probability model proves the universal zero-identification claim.')
    unknown_basis=None;zero_basis=F(0)
    require(unknown_basis is None and unknown_basis!=zero_basis,'unknown versus zero')
    record('8.1 unknown basis resolution','insufficiently specified',
           'Unknown is not numeric zero. Converting absent basis to zero requires a separately justified rule. Likewise, transfer classification and which records satisfy legal requirements are not determined by the vector representation.')



# Intended validation: Lemma 8.1 FIFO assertions.
# Implement quantity-aware FIFO with explicit unknown-basis rejection; compare
# chronological lot selection with gain-maximizing selection and test partial
# lots. Rates and legal admissibility are outside this arithmetic check.

from fractions import Fraction as F

def fifo(lots,amount):
    if amount<0:raise ValueError('negative quantity')
    if sum(x['quantity'] for x in lots)<amount:raise ValueError('insufficient quantity')
    selected=[];basis=F(0);remaining=amount
    for lot in sorted(lots,key=lambda x:x['date']):
        take=min(remaining,lot['quantity'])
        if take:
            if lot['basis'] is None:raise ValueError('unknown basis needs an external resolution rule')
            basis+=lot['basis']*take/lot['quantity'];selected.append((lot['id'],str(take)))
            remaining-=take
        if remaining==0:break
    return basis,selected

def validate_fifo_claims():
    lots=[dict(id='old',quantity=F(1),basis=F(100),date=1),dict(id='new',quantity=F(1),basis=F(10),date=2)]
    basis,selection=fifo(lots,F(1));proceeds=F(120)
    require(basis==100 and proceeds-basis==20,'FIFO gain')
    maximum=proceeds-min(x['basis'] for x in lots)
    require(maximum==110 and proceeds-basis<maximum,'not maximal gain')
    record('8.1 FIFO maximizes gain','contradicted',
           'FIFO orders by acquisition time, not cost. Selling one unit for 120 selects the older basis-100 lot and yields gain 20; selecting the newer basis-10 lot yields 110. FIFO is not universally gain-maximizing.',
           fifo_selection=selection,fifo_gain='20',maximum_example_gain='110')
    mixed=[dict(id='a',quantity=F(3),basis=F(90),date=1),dict(id='b',quantity=F(2),basis=F(100),date=2)]
    basis,selected=fifo(mixed,F(4))
    require(basis==140,'partial lot basis')
    record('8.1 partial-lot accounting','supported under stated assumptions',
           'Three units from a total-basis-90 lot plus one unit from a two-unit total-basis-100 lot allocate basis 140.',selected=selected,allocated_basis=str(basis))
    bad=[dict(id='unknown',quantity=F(1),basis=None,date=1)]
    try:fifo(bad,F(1))
    except ValueError:pass
    else:raise AssertionError('unknown basis silently used')
    record('8.1 FIFO implies zero basis','insufficiently specified',
           'Ordering known lots does not supply missing acquisition values. The example allocator explicitly rejects unknown basis instead of silently turning it into zero. The source needs an external rule to make that transition.')



# Intended validation: Theorem 8.2 integration and accumulator recurrence.
# Independently compare piecewise-constant integration, cumulative readings,
# unequal time weights, partial intervals, same-time updates and a linear
# price signal for which the discrete left rule is only an approximation.

from fractions import Fraction as F

def integral(points,start,end):
    if end<=start or start<points[0][0] or end>points[-1][0]:raise ValueError('invalid observation window')
    total=F(0)
    for (left,price),(right,_) in zip(points,points[1:]):
        duration=max(F(0),min(end,right)-max(start,left))
        total+=price*duration
    return total

def validate_twap_accumulator():
    points=[(F(0),F(100)),(F(10),F(200)),(F(40),F(50)),(F(60),F(50))]
    cumulative=[F(0)]
    for (a,price),(b,_) in zip(points,points[1:]):cumulative.append(cumulative[-1]+price*(b-a))
    area=integral(points,F(0),F(60));twap=area/60
    require(area==cumulative[-1]==8000 and twap==F(400,3),'integral accumulator agreement')
    partial=integral(points,F(5),F(50))/45
    require(partial==F(1400,9),'partial-bin integration')
    record('8.2 TWAP identity','supported under stated assumptions',
           'For the stated piecewise-constant process, cumulative differences equal the exact time integral and correctly weight unequal durations.',
           area=str(area),window_seconds=60,twap=str(twap),partial_window_twap=str(partial))
    sample_mean=F(100+200+50,3)
    require(sample_mean!=twap,'time weights matter')
    record('8.2 sample versus time average','supported under stated assumptions',
           'An unweighted sample mean differs from the time-weighted mean when intervals have unequal duration.',sample_mean=str(sample_mean),time_mean=str(twap))
    # P(t)=t on [0,2]: exact integral=2; one left-endpoint interval gives 0.
    exact=F(2);left_rule=F(0)*2
    require(exact!=left_rule,'continuous interpolation assumption')
    record('8.2 recurrence domain','insufficiently specified',
           'The discrete left-price recurrence is exact for a step-held price process. For a changing continuous price it is a numerical approximation unless additional integration data are supplied.',linear_signal_exact_area=str(exact),single_step_left_area=str(left_rule))
    require(F(999)*(10-10)==0,'same timestamp contributes no duration')
    for a,b in [(F(1),F(1)),(F(5),F(2))]:
        try:integral(points,a,b)
        except ValueError:pass
        else:raise AssertionError('invalid interval accepted')
    record('8.2 update and endpoint semantics','insufficiently specified',
           'Zero-duration updates add nothing, and a positive window is required. Uniswap v2 updates stored cumulative values when its update routine executes, using elapsed time and prior reserves; it is not an autonomous timer that runs each block. Boundary observations must be available or correctly extrapolated.')



# Intended validation: Theorem 8.2 robustness and real-time valuation claims.
# Use abstract price signals to quantify partial-window perturbation and
# averaging bounds; test look-ahead and reciprocal-price effects. These are
# offline signal examples, not a strategy or transaction implementation.

from fractions import Fraction as F

def validate_twap_sensitivity():
    baseline=F(100);window=F(1800);duration=F(60);changed_price=F(70)
    average=(baseline*(window-duration)+changed_price*duration)/window
    shift=(changed_price-baseline)*duration/window
    require(average==99 and shift==-1,'partial-window perturbation')
    record('8.2 full-window manipulation requirement','contradicted',
           'An average can change when the input changes for only part of its window. A 60-second price interval of 70 within an otherwise 100-valued 1800-second signal yields TWAP 99. Holding a changed price for all 30 minutes is not mathematically necessary for any effect.',
           baseline=str(baseline),duration_seconds=str(duration),window_seconds=str(window),average=str(average),shift=str(shift))
    bound=abs(changed_price-baseline)*duration/window
    require(abs(average-baseline)<=bound,'weighted perturbation bound')
    record('8.2 conditional damping','supported under stated assumptions',
           'If price deviation is bounded by M over at most d seconds in window T, average deviation is at most M*d/T. Averaging reduces short-duration influence but does not imply immunity.',bound=str(bound))
    past=F(100);future=F(200)
    centered=(past+future)/2
    require(centered==150 and centered!=past,'future dependence')
    record('8.2 centered-window availability','insufficiently specified',
           'A window from execution minus 15 minutes to execution plus 15 minutes needs future observations. It supports a later calculation, not an immediate fully observed valuation.',past_only_mean=str(past),centered_mean=str(centered))
    mean=(F(1)+F(4))/2;inverse_mean=(F(1)+F(1,4))/2
    require(1/mean!=inverse_mean,'reciprocal TWAP')
    record('8.2 quote direction','supported under stated assumptions',
           'Inverting a TWAP generally differs from averaging inverse prices. Direction and units must be chosen explicitly.',inverse_of_mean=str(1/mean),mean_of_inverse=str(inverse_mean))
    record('8.2 economic and statutory guarantees','insufficiently specified',
           'Economic prohibitivity and legal FMV require assumptions about liquidity, incentives, observation quality and valuation rules. No such guarantee follows from the integral itself; the reference pool TWAP can also differ from another market price.')



# Intended validation: Proposition 8.3 AMM output and invariant mechanics.
# Verify rational output substitution, domain and monotonicity; distinguish
# fee-adjusted reserves from actual reserves when fees remain in the pool,
# compare marginal and finite execution prices, and test integer rounding.

from fractions import Fraction as F

def output(x,y,dx,fee):
    if x<=0 or y<=0 or dx<0 or not 0<=fee<=1:raise ValueError('invalid AMM inputs')
    effective=dx*(1-fee)
    return y*effective/(x+effective)

def validate_constant_product():
    cases=0
    for x in [F(1),F(1000)]:
        for y in [F(2),F(2000)]:
            for dx in [F(0),F(1),F(100)]:
                for fee in [F(0),F(3,1000),F(1)]:
                    dy=output(x,y,dx,fee)
                    require((x+dx*(1-fee))*(y-dy)==x*y,'effective invariant')
                    require(0<=dy<y,'output bounds');cases+=1
    record('8.3 output identity','supported under stated assumptions',
           'Exact rational substitution verifies the effective-input constant-product formula and bounded output in all tested admissible cases.',cases=cases)
    x,y,dx,fee=F(1000),F(2000),F(100),F(3,1000)
    dy=output(x,y,dx,fee)
    old_k=x*y;actual_k=(x+dx)*(y-dy)
    require(actual_k>old_k,'fee-retained actual k grows')
    record('8.3 constant actual reserve product','contradicted',
           'If the fee remains in the pool, the actual input reserve receives the full input. Its product with the new output reserve exceeds the original product. Equality holds for effective fee-adjusted reserves, not actual balances in this model.',
           old_product=str(old_k),actual_new_product=str(actual_k),effective_output=str(dy))
    pre_spot=y/x;execution=dy/dx
    require(execution<pre_spot,'finite execution price')
    require(output(x,y,dx+1,fee)>dy,'input monotonicity')
    require(output(x,y,dx,F(1,100))<dy,'fee monotonicity')
    record('8.3 prices and comparative statics','supported under stated assumptions',
           'The finite output/input ratio is lower than the pre-swap reserve ratio for this positive trade. Output increases with input and decreases with fee. A finite trade ratio is not generally the marginal spot price.',
           marginal_pretrade_price=str(pre_spot),execution_ratio=str(execution))
    rounded=dy.numerator//dy.denominator
    require(0<=dy-rounded<1 and (x+dx*(1-fee))*(y-rounded)>=old_k,'rounding')
    record('8.3 atomic-unit rounding','supported under stated assumptions',
           'Rounding output down in integer atomic units gives less than one unit of output error and changes the effective invariant equality to an inequality.',exact_output=str(dy),integer_output=rounded)



# Intended validation: Proposition 8.3 combined AMM/TWAP gain expression.
# Compare direct and substituted proceeds, decimal-unit conversions, positive
# domain boundaries, and signed gain under alternative bases. Keep realization
# and zero-basis treatment separate from liquidity-pool arithmetic.

from fractions import Fraction as F

def validate_gain_valuation():
    x,y,dx,fee,price=F(1000),F(2000),F(100),F(3,1000),F(5)
    effective=dx*(1-fee);dy=y*effective/(x+effective)
    direct=dy*price
    substituted=y*dx*(1-fee)/(x+dx*(1-fee))*price
    require(direct==substituted and direct>0,'gain substitution')
    record('8.3 combined valuation identity','supported under stated assumptions',
           'Output times a fiat-per-output-token quote equals the substituted rational formula. Interpreting that amount as gain additionally assumes zero accepted basis.',output=str(dy),modeled_proceeds=str(direct))
    gain_zero=direct;gain_equal=direct-direct;gain_higher=direct-(direct+10)
    require(gain_equal==0 and gain_higher==-10,'basis dependence')
    record('8.3 strictly positive gain','insufficiently specified',
           'With positive reserves/input/price and fee below one, proceeds are positive. Gain still depends on accepted basis: equal basis gives zero and greater basis gives a loss. Zero input, zero price or fee one also gives zero proceeds in the mathematical extension.',
           zero_basis_gain=str(gain_zero),equal_basis_gain=str(gain_equal),greater_basis_gain=str(gain_higher))
    atoms=1500000;decimals=6;fiat_price=F(2)
    proper=F(atoms,10**decimals)*fiat_price;naive=atoms*fiat_price
    require(proper==3 and naive/proper==10**6,'token decimal conversion')
    record('8.3 valuation units','supported under stated assumptions',
           'A quote per whole token must multiply whole-token quantity. 1500000 atomic units with six decimals at 2 fiat per token is 3 fiat, not 3000000.',correct_proceeds=str(proper),unscaled_result=str(naive))
    record('8.3 realization and legal effect','insufficiently specified',
           'The bonding curve has no variables for taxable-event classification, holding-period law, admissible basis, or legal liability. The technical output identity cannot establish those premises; no current legal rule is validated here.')



# Run all validations; assertions signal failed checks, not contradicted claims.
def main():
    import argparse
    from collections import Counter
    parser = argparse.ArgumentParser(description='phase8 fifo twap and amm valuation validation')
    parser.add_argument("--output", type=Path, help="Also save the JSON report to this path.")
    args = parser.parse_args()
    RESULTS.clear()
    validate_lot_transfer()
    validate_fifo_claims()
    validate_twap_accumulator()
    validate_twap_sensitivity()
    validate_constant_product()
    validate_gain_valuation()
    report = dict(phase=8, python=platform.python_version(), scope="Synthetic mathematical validation; no legal findings.", conclusion="Phase 8 is not validated as a whole.", assessment_counts=dict(Counter(item["status"] for item in RESULTS)), results=RESULTS)
    payload = json.dumps(report, indent=2, allow_nan=False)
    if args.output:
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
