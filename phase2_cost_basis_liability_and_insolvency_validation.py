# Intended validation: Run all six original Phase 2 validation sections.
# Preserve their mathematical fixtures, counterexamples, assumptions and findings.
# Detailed intended-validation comments precede each section below.
# A successful run means all implementation checks completed; it does not mean
# every manuscript claim is supported. Findings retain their original statuses.
# Title: Phase 2 cost basis liability and insolvency validation
# Requires Python 3.9+; install dependencies: python -m pip install numpy scipy
# Run: python phase2_cost_basis_liability_and_insolvency_validation.py
# Save JSON: python phase2_cost_basis_liability_and_insolvency_validation.py --output phase2_results.json
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
import math
from fractions import Fraction
from scipy.integrate import solve_ivp

def require(condition, label):
    """Implementation self-check, not an assertion that the paper is correct."""
    if not condition:
        raise AssertionError(label)

def integrity(degrees):
    value = Fraction(1)
    for degree in degrees:
        if not isinstance(degree, int) or degree < 0:
            raise ValueError('Degrees must be nonnegative integers')
        value /= max(1, degree)
    return value

def exact_sum(principal, fee, depth):
    if not 0 <= fee <= 1 or depth < 0:
        raise ValueError('Fee must be in [0,1] and depth nonnegative')
    if fee == 0:
        return principal*depth
    q = 1-fee
    return principal*q*(1-q**depth)/fee

def liability(v, fee, multiplier, n):
    if fee == 0:
        return multiplier*v*n
    q=1-fee
    return multiplier*v*q*(1-q**n)/fee

def wealth(v, fee, offchain, n):
    return v*(1-fee)**n+offchain

def first_crossing(v, fee, multiplier, offchain):
    if v <= 0 or multiplier <= 0 or offchain < 0 or not 0 <= fee < 1:
        raise ValueError('Require V>0, multiplier>0, offchain>=0, and 0<=fee<1')
    if fee == 0:
        return int((v+offchain)//(multiplier*v))+1
    limit=multiplier*v*(1-fee)/fee
    if limit <= offchain:
        return None
    # Exact rational comparisons avoid floating equality errors at crossings.
    low,high=0,1
    while liability(v,fee,multiplier,high) <= wealth(v,fee,offchain,high):
        high *= 2
    while high-low > 1:
        middle=(low+high)//2
        if liability(v,fee,multiplier,middle) > wealth(v,fee,offchain,middle):
            high=middle
        else:
            low=middle
    return high

# Intended validation: Proposition 2.1 and Definitions 2.1.1–2.1.2.
# Check the inverse-degree product, exponential depth decay, threshold
# boundaries, numerical underflow, and adjusted-basis arithmetic. Separate
# the stipulated zero-basis rule from any derivation or legal justification.

def validate_basis_threshold():
    """Run this section with an independent findings list."""
    results = []

    def record(claim, status, explanation, **evidence):
        results.append(dict(claim=claim, status=status,
                            explanation=explanation, evidence=evidence))

    for depth in [0, 1, 5, 20, 100]:
        require(integrity([2]*depth) == Fraction(1, 2**depth), 'binary product')
    require(integrity([0, 1, 1]) == 1, 'empty and unbranched cases')
    record('2.1.1 degree product', 'supported under stated assumptions',
           'For D binary ancestors the metric is exactly 2^(-D); unbranched ancestors contribute one.',
           depth_20=str(integrity([2]*20)))
    epsilon = Fraction(1, 100)
    claimed = Fraction(1000)
    accepted = lambda value: claimed if value >= epsilon else Fraction(0)
    require(accepted(epsilon) == claimed and accepted(epsilon-Fraction(1,100000)) == 0, 'threshold boundary')
    record('2.1.2 threshold arithmetic', 'supported under stated assumptions',
           'The definition is a discontinuous rule: equality accepts all claimed basis; values below the threshold accept none. This implements an assumption rather than proving it.',
           at_threshold=str(accepted(epsilon)), below_threshold='0')
    # A degree-two split whose identified target branch has probability .99
    # is compatible with the same topology as a fair .5/.5 split.
    record('2.1.1 probability interpretation', 'insufficiently specified',
           'Topology alone does not supply branch probabilities or evidentiary quality. Identical degree-two graphs may have target-branch probabilities .5 or .99, or complete transaction records.',
           structural_value=str(integrity([2])), alternative_target_probabilities=[.5,.99,1.])
    c, entropy = 2., 10.
    probability = math.exp(-c*entropy)
    # A random valid/invalid-records model does not force the accepted basis
    # in an individual valid-records outcome to equal its expectation.
    record('2.1 exponential admissibility model', 'insufficiently specified',
           'The entropy measure, proportionality constant, regulatory scale, and threshold are unspecified. A probability tending to zero does not itself define accepted basis or prove an individual deterministic zero-basis decision.',
           illustrative_probability=probability,
           conditional_basis_if_records_valid=1000,
           illustrative_expected_basis=1000*probability)
    starting = Fraction(100)
    adjustments = [Fraction(5), Fraction(-2), Fraction(8)]
    basis = starting + sum(adjustments)
    proceeds, rate = Fraction(150), Fraction(1,5)
    require(basis == 111 and (proceeds-basis)*rate == Fraction(39,5), 'basis adjustments')
    require(proceeds*rate == 30, 'zero-basis substitution')
    record('2.1 basis and liability identities', 'supported under stated assumptions',
           'Basis adjustments sum to 111; a stipulated zero basis gives proceeds times rate. No rule connecting graph entropy to legally accepted basis is established by these identities.',
           adjusted_basis=str(basis), ordinary_model_liability=str((proceeds-basis)*rate),
           zero_basis_model_liability=str(proceeds*rate))
    exact = integrity([2]*1100)
    require(exact > 0 and float(exact) == 0., 'underflow fixture')
    record('2.1 numerical stability', 'supported under stated assumptions',
           'Use exact rationals or log-integrity: binary depth 1100 is positive mathematically but underflows in a float.',
           log_integrity=-1100*math.log(2), floating_integrity=float(exact))
    return results


# Intended validation: Lemma 2.2.
# Test zero-basis summation, event deduplication, gain clipping, acquisition
# basis alternatives, and the distinction between additivity and statistical
# independence. Legal event classification remains an explicit model input.

def validate_swap_accounting():
    """Run this section with an independent findings list."""
    results = []

    def record(claim, status, explanation, **evidence):
        results.append(dict(claim=claim, status=status,
                            explanation=explanation, evidence=evidence))

    rate = Fraction(1,5)
    values = [Fraction(100), Fraction(90), Fraction(80)]
    require(rate*sum(values) == 54, 'zero-basis sum')
    record('2.2 zero-basis sum', 'supported under stated assumptions',
           'For three separately classified events with values 100, 90, 80, zero basis and rate .2 give modeled liability 54.',
           liability=54)
    # Same proceeds, two different assumptions about acquired-asset basis.
    gains = [Fraction(100)-100, Fraction(90)-100, Fraction(80)-90]
    require(sum(gains) == -20, 'gain telescoping')
    record('2.2 resetting basis', 'insufficiently specified',
           'Zero basis at every subsequent swap is an additional assumption. In a hypothetical model assigning acquired assets the preceding exchange value, the same sequence has signed gains 0, -10, -10. This is a mathematical comparison, not a tax-law determination.',
           repeated_zero_basis_gains=[100,90,80], alternative_signed_gains=[int(g) for g in gains])
    signed = Fraction(80)-100
    clipped = max(Fraction(0), signed)
    require(signed == -20 and clipped == 0, 'clipped loss')
    record('2.2 gain clipping and positivity', 'insufficiently specified',
           'max(0, proceeds-basis) suppresses losses; it is not the signed gain identity. Strict positivity also requires strictly positive proceeds. Its aggregate use needs explicit loss and event rules.',
           signed_gain=int(signed), clipped_gain=int(clipped))
    events = [('swap_1',100),('swap_1',100),('swap_2',90)]
    unique = dict(events)
    raw = rate*sum(Fraction(v) for _,v in events)
    deduplicated = rate*sum(Fraction(v) for v in unique.values())
    require(raw == 58 and deduplicated == 38, 'event duplicate')
    record('2.2 graph edges and dispositions', 'insufficiently specified',
           'A single execution may have several transfer edges. One-to-one event attribution and a classification policy are needed before summing edge values. A changed asset identifier alone does not encode that policy.',
           raw_edge_sum_liability=str(raw), unique_event_liability=str(deduplicated))
    # Two event values X and Y share the same random factor: Y=X.
    x = [Fraction(0),Fraction(2)]
    mean = sum(x)/2
    covariance = sum((v-mean)**2 for v in x)/2
    require(covariance == 1, 'dependent events')
    record('2.2 independence', 'contradicted',
           'Being distinct events does not imply statistical independence. X=Y with equiprobable values 0 and 2 has covariance 1. Additivity of an assessed sum does not need independence.',
           covariance=str(covariance))
    return results


# Intended validation: Lemma 2.2 geometric liability and its linear approximation.
# Compare exact rational summation with the closed form; test fee boundaries,
# monotonicity, finite saturation, and approximation error as depth increases.

def validate_geometric_growth():
    """Run this section with an independent findings list."""
    results = []

    def record(claim, status, explanation, **evidence):
        results.append(dict(claim=claim, status=status,
                            explanation=explanation, evidence=evidence))

    cases = 0
    for fee in [Fraction(0),Fraction(1,1000),Fraction(1,10),Fraction(1)]:
        for depth in [0,1,2,10,100]:
            direct = sum((Fraction(100)*(1-fee)**k for k in range(1,depth+1)), Fraction(0))
            require(exact_sum(Fraction(100),fee,depth) == direct, 'geometric identity')
            cases += 1
    record('2.2 exact series', 'supported under stated assumptions',
           'Sum k=1..N of V0*q^k is V0*q*(1-q^N)/(1-q). Fee zero gives V0*N and fee one gives zero.',
           exact_cases=cases)
    rows = []
    for fee in [Fraction(1,1000),Fraction(1,100),Fraction(1,10)]:
        for depth in [1,10,100,1000]:
            exact = exact_sum(Fraction(100),fee,depth)
            linear = Fraction(100*depth)
            require(exact <= linear, 'linear upper bound')
            rows.append(dict(fee=float(fee),depth=depth,exact=float(exact),linear=float(linear),
                             relative_overestimate=float((linear-exact)/exact)))
    record('2.2 linear approximation range', 'insufficiently specified',
           'A small per-hop fee alone is insufficient at large depth. The first-order relative loss from V0*N is approximately fee*(N+1)/2, requiring cumulative fee-depth effects to be small.',
           examples=rows)
    fee, principal, rate = Fraction(1,10), Fraction(100), Fraction(1,5)
    limit = rate*principal*(1-fee)/fee
    for n in [0,1,10,100]:
        delta = rate*(exact_sum(principal,fee,n+1)-exact_sum(principal,fee,n))
        require(delta == rate*principal*(1-fee)**(n+1) and delta > 0, 'positive increment')
    record('2.2 asymptotic growth', 'contradicted',
           'With fixed fee in (0,1), liability increases with diminishing increments and approaches a finite limit. It is neither asymptotically linear nor exponentially increasing in depth.',
           limit=float(limit), liability_depth_1000=float(rate*exact_sum(principal,fee,1000)))
    return results


# Intended validation: Definitions 2.2.1–2.2.2.
# Compare the four-index contraction to an independent event ledger; test
# price units, event-specific swap masks, temporal aggregation error, and
# dependence on zero-basis/nonnegative-price modeling assumptions.

def validate_liability_tensor():
    """Run this section with an independent findings list."""
    results = []

    def record(claim, status, explanation, **evidence):
        results.append(dict(claim=claim, status=status,
                            explanation=explanation, evidence=evidence))

    # source, destination, asset, epoch, quantity, is_swap
    events = [(0,1,0,0,2.,True),(1,2,1,1,3.,True),(0,2,0,1,4.,False)]
    prices = np.array([[100.,110.],[20.,25.]])
    tensor = np.zeros((3,3,2,2))
    omega = np.zeros((3,3))
    for i,j,a,k,amount,swap in events:
        tensor[i,j,a,k] += amount
        omega[i,j] = float(swap)
    rate=.2
    contraction = rate*np.einsum('ijak,ij,ak->',tensor,omega,prices)
    ledger = rate*sum(amount*prices[a,k] for i,j,a,k,amount,swap in events if swap)
    require(np.isclose(contraction,ledger) and np.isclose(ledger,55), 'tensor-ledger agreement')
    record('2.2.2 contraction', 'supported under stated assumptions',
           'For unambiguous pair-level swap labels, token quantities, fiat-per-token prices, and zero basis, the contraction equals an independent event sum.',
           contraction=float(contraction), event_sum=float(ledger))
    require(2*100 == 200 and 2*200 == 400, 'price units')
    record('2.2 oracle signature and units', 'insufficiently specified',
           'The prose alternates between a volume valuation M(asset,volume,time) and a price matrix. The tensor requires fiat per token; multiplying quantity by an already-total fiat valuation double counts quantity.',
           correct_fiat=200, double_quantity_fiat=400)
    # This matters if events sharing a source/destination pair are aggregated.
    pair_events = [(2.,True),(3.,False)]
    true_value = sum(q*100 for q,s in pair_events if s)
    mask_one = sum(q*100 for q,s in pair_events)
    require(true_value == 200 and mask_one == 500, 'mixed pair mask')
    record('2.2.1 mask resolution', 'insufficiently specified',
           'If the normalized representation allows a pair to contain both swap and non-swap events, a single Omega[i,j] cannot classify them. Keep event-level labels or an asset/time-resolved mask. Unique event-state pairs can avoid this issue.',
           correct_value=true_value, pair_mask_one_value=mask_one, pair_mask_zero_value=0)
    quantities=np.array([1.,9.])
    event_prices=np.array([100.,200.])
    exact=float(quantities@event_prices)
    bin_average=float(quantities.sum()*event_prices.mean())
    weighted=float(quantities.sum()*np.average(event_prices,weights=quantities))
    require(exact == 1900 and bin_average == 1500 and weighted == exact, 'epoch pricing')
    record('2.2.2 temporal price aggregation', 'insufficiently specified',
           'Epoch-level prices reproduce exact event valuations only under suitable constancy or weighting assumptions; an unweighted average may misvalue unequal trade sizes.',
           exact_value=exact, average_price_value=bin_average, volume_weighted_value=weighted)
    return results


# Intended validation: Theorem 2.3.
# Retain the exact fee-decaying series when comparing liability and wealth.
# Derive the condition for a finite crossing, verify integer thresholds, and
# test the claimed universal insolvency conclusion against a counterexample.

def validate_insolvency_threshold():
    """Run this section with an independent findings list."""
    results = []

    def record(claim, status, explanation, **evidence):
        results.append(dict(claim=claim, status=status,
                            explanation=explanation, evidence=evidence))

    v,fee,multiplier = Fraction(100),Fraction(1,10),Fraction(7,20)
    limit=multiplier*v*(1-fee)/fee
    offchain=Fraction(400)
    require(limit == 315 and first_crossing(v,fee,multiplier,offchain) is None, 'no-crossing counterexample')
    n=15
    linear=multiplier*v*n
    exact=liability(v,fee,multiplier,n)
    assets=wealth(v,fee,offchain,n)
    require(linear > v+offchain and exact < assets, 'linear approximation changes conclusion')
    record('2.3 universal insolvency', 'contradicted',
           'At V0=100, fee=.1, rate=.2, fraud factor=1.75 and no interest, exact debt is always below 315 while off-chain assets alone are 400. No finite crossing exists. The linear approximation incorrectly predicts insolvency beyond about 14.286 hops.',
           liability_limit=float(limit), offchain_assets=float(offchain),
           depth=n, linear_debt=float(linear), exact_debt=float(exact), remaining_wealth=float(assets))
    small_fee=Fraction(1,1000)
    large_offchain=Fraction(40000)
    small_fee_limit=multiplier*v*(1-small_fee)/small_fee
    require(small_fee_limit == 34965 and first_crossing(v,small_fee,multiplier,large_offchain) is None,
            'small-fee no-crossing example')
    record('2.3 small-fee robustness', 'contradicted',
           'The no-crossing counterexample also works with a small fee of .001: debt approaches 34965, below off-chain wealth of 40000. Small per-hop friction does not justify extending the linear approximation to arbitrary depth.',
           fee=float(small_fee), liability_limit=float(small_fee_limit), offchain_assets=float(large_offchain))
    rows=[]
    for b in [Fraction(0),Fraction(100),Fraction(300),Fraction(315),Fraction(400)]:
        crossing=first_crossing(v,fee,multiplier,b)
        if crossing is not None:
            require(liability(v,fee,multiplier,crossing)>wealth(v,fee,b,crossing), 'crossing')
            require(liability(v,fee,multiplier,crossing-1)<=wealth(v,fee,b,crossing-1), 'minimal crossing')
            ratio=(limit-b)/(limit+v)
            continuous=math.log(float(ratio))/math.log(float(1-fee))
        else:
            continuous=None
        rows.append(dict(offchain=float(b),first_integer_crossing=crossing,continuous_equality_depth=continuous))
    record('2.3 conditional exact threshold', 'supported under stated assumptions',
           'Let q=1-fee and A=multiplier*V0*q/fee. Under the equality wealth model, a finite crossing exists iff A>offchain. Then q^N<(A-offchain)/(A+V0). Exact rational comparisons verify the smallest integer crossing.',
           examples=rows)
    require(first_crossing(v,Fraction(0),multiplier,Fraction(400)) == 15, 'zero-fee threshold')
    bound=(v+offchain)/(multiplier*v)
    record('2.3 linear-model threshold', 'supported under stated assumptions',
           'W0/(multiplier*V0) is a sufficient debt>initial-wealth bound within the linear model, not generally the equality depth against declining wealth. The zero-fee model gives exact crossing at the next integer above this ratio.',
           bound=float(bound), zero_fee_first_crossing=15)
    record('2.3 wealth upper bound', 'insufficiently specified',
           'The document bounds actual wealth above by V0*q^N+offchain. Exceeding this upper bound suffices for insolvency; failing to exceed it does not prove solvency. The counterexample chooses equality, which satisfies the stated model.')
    return results


# Intended validation: Theorem 2.3 and Definitions 2.3.1–2.3.2.
# Check the continuous-interest ODE and epoch matrix independently; test
# zero rates, distinct accrual dates, partial penalty applicability, and the
# difference between continuous and daily compounding. No statutory rate,
# accrual date, fraud finding, or enforcement authorization is inferred.

def validate_penalty_interest_accrual():
    """Run this section with an independent findings list."""
    results = []

    def record(claim, status, explanation, **evidence):
        results.append(dict(claim=claim, status=status,
                            explanation=explanation, evidence=evidence))

    initial=175.
    # Piecewise-constant annual rates with all times in years.
    times=np.array([0.,1.,2.,3.])
    rates=np.array([.05,.08,.03])
    analytic=initial*math.exp(float(rates@np.diff(times)))
    numerical=initial
    for left,right,rate in zip(times[:-1],times[1:],rates):
        solution=solve_ivp(lambda t,y:rate*y,(left,right),[numerical],rtol=1e-11,atol=1e-12)
        require(solution.success, 'ODE solver success')
        numerical=float(solution.y[0,-1])
    require(math.isclose(analytic,numerical,rel_tol=1e-10), 'integral vs ODE')
    record('2.3 continuous interest', 'supported under stated assumptions',
           'The ODE dL/dt=r(t)L has the stated exponential integral solution when no additional liabilities are introduced within the interval.',
           analytic=analytic, independent_ODE=numerical, absolute_difference=abs(analytic-numerical))
    cumulative=np.r_[0.,np.cumsum(rates*np.diff(times))]
    matrix=np.zeros((4,4))
    for k in range(4):
        for j in range(k,4):
            matrix[k,j]=math.exp(float(cumulative[j]-cumulative[k]))
    liabilities=np.array([100.,50.,25.,0.])
    rho=.75
    demand=float((1+rho)*(liabilities@matrix[:,-1]))
    recurrence=liabilities[0]*(1+rho)
    for j in range(1,4):
        recurrence=recurrence*math.exp(rates[j-1]*(times[j]-times[j-1]))+(1+rho)*liabilities[j]
    require(np.allclose(np.diag(matrix),1) and np.all(matrix[np.tril_indices(4,-1)]==0), 'matrix structure')
    require(math.isclose(demand,recurrence,rel_tol=1e-12), 'matrix vs chronological accrual')
    record('2.3.1–2.3.2 accrual contraction', 'supported under stated assumptions',
           'The terminal-column contraction matches a chronological accrual recurrence, given shared penalty rates and explicitly specified liability start times.',
           matrix_demand=demand, recurrence_demand=float(recurrence), matrix=matrix.tolist())
    all_at_start=float((1+rho)*liabilities.sum()*math.exp(cumulative[-1]))
    require(all_at_start > demand, 'distinct start dates')
    record('2.3 common start date', 'insufficiently specified',
           'Accruing all obligations from a single date differs from per-epoch accrual. Transaction epochs and accrual start dates cannot be equated without an external rule.',
           common_start_demand=all_at_start, separate_start_demand=demand)
    base,attributable,rho=100.,40.,.75
    blanket=base*(1+rho)
    portion=base+rho*attributable
    require(blanket == 175 and portion == 130, 'partial penalty')
    record('2.3 penalty applicability', 'insufficiently specified',
           'Applying a multiplier to the entire base presumes the entire base is penalty-eligible. If an input model marks only 40 of 100 as eligible, a .75 penalty produces 130, not 175.',
           full_base_penalty_total=blanket, partial_base_penalty_total=portion)
    continuous=100*math.exp(.1)
    daily=100*(1+.1/365)**365
    require(continuous > daily, 'compounding conventions')
    zero_rate=float((1+.75)*liabilities.sum())
    require(np.isclose(zero_rate,306.25), 'zero-rate total')
    record('2.3 compounding convention', 'insufficiently specified',
           'Continuous and daily compounding differ. This comparison does not establish which convention any statute requires; rates, day counts, start dates, and penalty-interest treatment must be supplied.',
           continuous_one_year=continuous, daily_one_year=daily, zero_rate_demand=zero_rate)
    record('2.3.2 enforcement inference', 'insufficiently specified',
           'The demand scalar calculates a model amount. It has no mathematical input or predicate establishing a fraud finding or authorization for enforcement.')
    return results


VALIDATORS = (
    ('01_basis_threshold', validate_basis_threshold),
    ('02_swap_accounting', validate_swap_accounting),
    ('03_geometric_growth', validate_geometric_growth),
    ('04_liability_tensor', validate_liability_tensor),
    ('05_insolvency_threshold', validate_insolvency_threshold),
    ('06_penalty_interest_accrual', validate_penalty_interest_accrual),
)

def run_all():
    """Run every section and return one structured report; safe to call again."""
    sections = [dict(section=name, results=validate()) for name, validate in VALIDATORS]
    counts = Counter(item['status'] for section in sections for item in section['results'])
    return dict(title='Phase 2 cost basis liability and insolvency validation', script=Path(__file__).name,
                environment=dict(python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__),
                scope="Mathematical fixtures only; no real identity or legal findings.",
                summary=dict(sections=len(sections), findings=sum(counts.values()),
                             status_counts=dict(counts)), sections=sections)


def main():
    parser = argparse.ArgumentParser(description='Phase 2 cost basis liability and insolvency validation')
    parser.add_argument('--output', type=Path, help='Also save the JSON report to this path.')
    args = parser.parse_args()
    report = json.dumps(run_all(), indent=2, allow_nan=False)
    if args.output is not None:
        args.output.write_text(report + '\n', encoding='utf-8')
    print(report)


if __name__ == '__main__':
    main()
