# Intended validation: phase7 graph contraction and routing validation.
# Run all original phase checks and emit one JSON report.
# Successful execution confirms checks ran, not that all source claims hold.
# Usage: python phase7_graph_contraction_and_routing_validation.py --output phase7_results.json
# Dependency: NumPy (install with python -m pip install numpy).

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


# Intended validation: Proposition 7.1 and Theorem 7.3 mapping claims.
# Exhaustively check homomorphisms and isomorphisms for small directed graphs;
# distinguish edge preservation, bijection, cycles and weighted objectives.
# Synthetic graph countermodels do not classify actual legal structures.

from itertools import product,permutations

def homomorphism(edges,target,mapping):
    return all((mapping[u],mapping[v]) in target for u,v in edges)

def validate_graph_mappings():
    # A fork maps to a single edge by merging its two leaves.
    fork={(0,1),(0,2)};target={(0,1)};mapping={0:0,1:1,2:1}
    require(homomorphism(fork,target,mapping),'valid merging homomorphism')
    require(len(set(mapping.values()))<len(mapping),'noninjective example')
    record('7.1 homomorphism versus isomorphism','supported under stated assumptions',
           'An explicit edge-preserving map exists for this fork-to-edge example, but it merges vertices and is not an isomorphism.',mapping=mapping)
    # A directed path of three edges has no homomorphism into a one-edge
    # directed graph with no loops, despite both being acyclic.
    path={(0,1),(1,2),(2,3)}
    maps=[dict(enumerate(labels)) for labels in product(range(2),repeat=4)]
    count=sum(homomorphism(path,target,m) for m in maps)
    require(count==0,'nonexistence countermodel')
    record('7.1 asserted mapping existence','insufficiently specified',
           'Naming node and edge analogies does not ensure an edge-preserving map for arbitrary graphs. A length-three directed path has no homomorphism into a single directed edge without loops. Actual vertex sets, edges and a mapping are required.',
           mappings_exhaustively_checked=len(maps),valid_mappings=count)
    cycle={(0,1),(1,2),(2,0)};dag={(0,1),(1,2),(0,2)}
    isomorphic=any({(perm[u],perm[v]) for u,v in cycle}==dag for perm in permutations(range(3)))
    require(not isomorphic,'cycle versus DAG')
    record('7.1–7.3 strict topological equivalence','contradicted',
           'A directed cyclic corporate graph and an event-level DAG cannot be isomorphic. Both have three vertices and three edges in this exhaustive example. An entity-level cyclic graph and a time-expanded graph require different representations.',
           checked_bijections=6,isomorphic=isomorphic)
    record('7.1 metric and legal equivalence','insufficiently specified',
           'An unweighted edge-preserving map does not preserve money-valued price deviations, dimensionless KL divergence, ownership, utility or tax treatment. No transformations preserving those quantities are supplied.')



# Intended validation: Definition 7.1.1.
# Verify Hadamard row sums, zero-deviation behavior, cancellation, dimensions,
# and conservation. Distinguish gross outgoing deviations from a net transfer
# allocation and from removal of edges in an underlying transaction graph.

import numpy as np

def validate_shift_matrix():
    t=np.array([[0.,100.,20.],[30.,0.,40.],[10.,50.,0.]])
    e=np.array([[0.,.1,-.5],[-.2,0.,.25],[.3,-.1,0.]])
    h=t*e;s=h@np.ones(3)
    manual=np.array([sum(t[i,j]*e[i,j] for j in range(3)) for i in range(3)])
    require(np.allclose(s,manual) and np.allclose(s,[0.,4.,-2.]),'Hadamard row sums')
    require(np.allclose((t*np.zeros_like(e))@np.ones(3),0),'zero deviations')
    record('7.1.1 row-sum identity','supported under stated assumptions',
           'The displayed matrix operation equals row-wise sums of volume times deviation; zeroing the deviation matrix makes the resulting vector zero.',
           deviation_flows=h.tolist(),row_sum=s.tolist())
    require(s[0]==0 and np.any(h[0]!=0),'signed cancellation')
    record('7.1.1 zero vector converse','insufficiently specified',
           'A zero component can arise from cancellation of opposite signed deviations, not absence of deviations. Signs and interpretation of elasticity must be defined.',
           first_row_flows=h[0].tolist(),first_row_sum=float(s[0]))
    net=h.sum(axis=0)-h.sum(axis=1)
    require(np.isclose(net.sum(),0) and not np.isclose(s.sum(),0),'net conservation')
    record('7.1.1 net allocation semantics','insufficiently specified',
           'The source computes outgoing row sums, not a conservative net balance adjustment. For a transfer-flow interpretation, incoming minus outgoing has zero total, while the displayed vector need not.',
           source_vector_total=float(s.sum()),alternative_net_vector=net.tolist(),alternative_total=float(net.sum()))
    require(np.count_nonzero(t)==6,'unchanged edges')
    record('7.1.1 eliminating topology','contradicted',
           'Setting E to zero makes T Hadamard E zero but leaves T and its six transaction edges unchanged. This algebraic change is not node clustering, edge contraction or graph isomorphism.',remaining_transaction_edges=6)
    record('7.1.1 units','insufficiently specified',
           'If E is a currency price difference, quantity times E yields currency. If E is dimensionless elasticity, T must carry currency units for the same interpretation. No operational definition reconciles these alternatives or proves a legal reallocation rule.')



# Intended validation: Lemma 7.2 and Definition 7.2.1.
# Check the conditional negative-cost identity, zero-cost boundary, omitted
# benefits, threshold boundaries and feature-unit sensitivity. Do not infer
# a legal doctrine from a synthetic scalar utility or binary classifier.

import numpy as np

def validate_utility_indicator():
    gas,slippage=2.,3.;cost_only=-gas-slippage
    require(cost_only==-5 and -0.-0.==0,'cost formula and boundary')
    record('7.2 utility sign','supported under stated assumptions',
           'If all benefits are assumed zero and total cost is strictly positive, cost-only utility is negative. With both costs zero it is zero, not strictly negative.',positive_cost_utility=cost_only,zero_cost_utility=0)
    benefit=10.;full=benefit-gas-slippage
    require(full>0,'omitted benefit countermodel')
    record('7.2 zero duration implies no benefit','insufficiently specified',
           'A vanishing holding period or hedged market exposure does not constrain every benefit term to zero. An instantaneous service with benefit 10 and costs 5 has positive utility in a valid synthetic model.',benefit=benefit,net_utility=full)
    w=np.array([1.,0.,0.]);seconds=np.array([3600.,0.,0.]);days=np.array([1/24,0.,0.])
    threshold=1.
    decision=lambda u:int(w@u>threshold)
    require(decision(seconds)==1 and decision(days)==0,'unit sensitivity')
    require(decision(np.array([1.,0.,0.]))==0,'strict threshold')
    record('7.2.1 indicator boundary','supported under stated assumptions',
           'The displayed strict greater-than rule returns zero at equality, for fixed numerical units and weights.')
    record('7.2.1 units and calibration','insufficiently specified',
           'Expressing the same duration in seconds or days changes the score under unchanged weights. Weights must transform with feature units, or features must be normalized; weights and threshold are not specified.',seconds_decision=decision(seconds),days_decision=decision(days))
    record('7.2 legal inference','insufficiently specified',
           'Negative realized or modeled utility does not by itself encode intent, other benefits or the elements of a legal test. The indicator is a proposed classifier, not a proof of legal economic substance.')



# Intended validation: Definition 7.2.2.
# Evaluate the intended (A diag(1-chi))^m limit on a path, cycle and weighted
# loop; test the alternate A diag(1-chi)^m reading too. Compare with explicit
# elimination that connects retained endpoints through removed vertices.
# A_valid is not defined in the source; fixtures use retained original edges.

import numpy as np

def validate_contraction_operator():
    a=np.array([[0.,1.,0.],[0.,0.,1.],[0.,0.,0.]])
    chi=np.array([1,0,1]);d=np.diag(1-chi);b=a@d
    require(b[0,1]==1 and b[1,2]==0,'mask orientation')
    require(np.all(np.linalg.matrix_power(b,2)==0),'nilpotent limit')
    retained=[0,2];removed=[1]
    arr=a[np.ix_(retained,retained)]
    are=a[np.ix_(retained,removed)];aer=a[np.ix_(removed,retained)]
    corrected=arr+are@aer
    require(corrected[0,1]==1,'direct endpoint edge')
    record('7.2.2 path contraction','contradicted',
           'For 0->1->2 with chi=(1,0,1), the stated matrix-power limit is zero. With A_valid containing only pre-existing retained-to-retained edges, no 0->2 shortcut is created. Explicit elimination gives that edge.',
           masked_adjacency=b.tolist(),power_two=np.linalg.matrix_power(b,2).tolist(),
           retained_endpoint_adjacency=corrected.tolist())
    require(np.array_equal(a@np.linalg.matrix_power(d,20),b),'alternate mask power')
    record('7.2.2 mask interpretation','contradicted',
           'Right multiplication by diag(1-chi) preserves columns for chi=0 and zeros columns for chi=1, rather than deleting the zero-substance vertices. Reading the expression as A*diag(1-chi)^m gives the same non-contracting mask for all m>=1.')
    cycle=np.array([[0,1],[1,0]])
    require(np.array_equal(np.linalg.matrix_power(cycle,2),np.eye(2)) and not np.array_equal(cycle,np.eye(2)),'oscillation')
    weighted=np.array([[2]],dtype=object)
    require(np.linalg.matrix_power(weighted,10)[0,0]==1024,'divergence')
    record('7.2.2 existence of limit','insufficiently specified',
           'On arbitrary cyclic graphs the limit need not exist: a two-cycle oscillates, and a weight-two loop diverges. If Phase 1 acyclicity is retained, the masked matrix is nilpotent and its limit is zero, still not the desired shortcut operator.',
           cycle_power_1=cycle.tolist(),cycle_power_2=np.linalg.matrix_power(cycle,2).tolist(),weighted_power_10=1024)
    record('7.2.2 conditional elimination alternative','supported under stated assumptions',
           'For the tested acyclic path, retained adjacency plus A_RE*A_ER implements one-vertex elimination. For a general eliminated DAG use a finite path sum through its eliminated subgraph. Reachability should use Boolean operations; weighted path products need specified semantics.')
    record('7.2.2 missing A_valid definition','insufficiently specified',
           'An A_valid chosen to already contain every desired shortcut could supply the answer, but then the limit did not compute it. Vertex removal, indexing, weights and the construction of A_valid must be explicit.')



# Intended validation: Theorem 7.3 product objectives.
# Compare minimizing retention with minimizing total proportional loss;
# test event-risk assumptions, repeated cycles and abstract rate floors.
# All values are synthetic model inputs, not current taxes or bridge risks.

from fractions import Fraction as F
from math import prod,log

def validate_routing_objectives():
    rates={'low_loss':[F(1,100),F(1,100)],'high_loss':[F(2,5)]}
    retention={name:prod(1-r for r in path) for name,path in rates.items()}
    paper=min(retention,key=retention.get);least_loss=max(retention,key=retention.get)
    require(paper=='high_loss' and least_loss=='low_loss','objective reversal')
    record('7.3 tax objective direction','contradicted',
           'With W defined as proportional tax rates on remaining value, product(1-W) is retained value. Minimizing it selects the larger tax loss. Minimizing loss instead maximizes retention, or minimizes the sum of -log(1-W).',
           retention={k:str(v) for k,v in retention.items()},paper_choice=paper,minimum_loss_choice=least_loss)
    costs={name:sum(-log(float(1-r)) for r in path) for name,path in rates.items()}
    require(min(costs,key=costs.get)==least_loss,'log objective equivalence')
    record('7.3 conditional log transformation','supported under stated assumptions',
           'For factors in (0,1], maximizing their product is equivalent to minimizing negative log costs. A rate of one requires separate infinite-cost handling.',negative_log_costs=costs)
    marginal=F(1,10);independent_no_event=(1-marginal)**2;shared_no_event=1-marginal
    require(independent_no_event!=shared_no_event,'dependence counterexample')
    record('7.3 risk objective semantics','insufficiently specified',
           'If C is an adverse-event probability, a product of survival factors needs independence or conditional hazard factors. Equal marginals with perfectly shared events give .9 survival, not .81. If C is only a score, neither interpretation follows.',
           independent_survival=str(independent_no_event),shared_event_survival=str(shared_no_event))
    loop=F(9,10)
    require(loop**20<loop,'cycle preference')
    record('7.3 allowed paths','insufficiently specified',
           'If repeated walks are allowed, minimizing a retention product can favor endlessly repeating a lossy cycle, with infimum zero. A simple-path restriction or a different objective is needed.',
           one_loop_retention=str(loop),twenty_loop_retention=float(loop**20))
    floor=F(15,100);two_edge_loss=1-(1-floor)**2
    require(two_edge_loss==F(111,400),'edge floor aggregation')
    record('7.3 edge floor versus aggregate minimum','insufficiently specified',
           'Even as pure mathematics, replacing every edge rate by at least .15 is not the same operation as imposing an aggregate .15 effective-rate floor. Two .15 edges give total proportional loss .2775 in this model. No claim about actual policy is made.',
           edge_floor=str(floor),two_edge_aggregate_loss=str(two_edge_loss))



# Intended validation: Theorem 7.3 strict optimization equivalence and
# consistency of Lemma 7.2 contraction with earlier per-event liability.
# Test weighted objective preservation, bijection requirements, classification
# information versus causal intervention, and post-contraction accounting.

from fractions import Fraction as F

def validate_equivalence_and_consistency():
    # Same topology, two routes; relabeling vertices preserves edges but
    # does not preserve values unless edge costs are mapped as well.
    edges={(0,1),(1,3),(0,2),(2,3)}
    corp={(0,1):F(99,100),(1,3):F(99,100),(0,2):F(4,5),(2,3):F(4,5)}
    crypto={(0,1):F(4,5),(1,3):F(4,5),(0,2):F(99,100),(2,3):F(99,100)}
    paths=[[(0,1),(1,3)],[(0,2),(2,3)]]
    values=lambda weights:[weights[path[0]]*weights[path[1]] for path in paths]
    c,k=values(corp),values(crypto)
    require(set(corp)==edges==set(crypto) and c.index(max(c))!=k.index(max(k)),'weighted identity mapping fails')
    record('7.3 form versus optimization equivalence','insufficiently specified',
           'Identical objective syntax and even identical graph topology do not make a specified vertex mapping cost-preserving. Under the identity mapping, the best route reverses when weights are swapped. A cost-preserving path bijection must be exhibited; another relabeling may work for particular fixtures.',
           corporate_retention=[str(x) for x in c],crypto_retention=[str(x) for x in k])
    remapped=[k[1],k[0]]
    require(remapped==c,'explicit route bijection succeeds')
    record('7.3 conditional equivalence','supported under stated assumptions',
           'For this symmetric fixture, explicitly swapping intermediate vertices and their edge weights preserves both route objectives. This demonstrates what an actual equivalence proof must specify, not equivalence of real networks.')
    rate=F(1,5);penalty=F(7,4);events=[F(100),F(99),F(98)]
    per_event=sum(events)*rate*penalty;contracted=events[-1]*rate*penalty
    require(per_event!=contracted,'contraction changes modeled tax sum')
    record('7.2 versus earlier liability sum','insufficiently specified',
           'Replacing three zero-basis dispositions by one endpoint disposition changes the earlier per-event liability functional. The paper must explain whether contraction only changes visualization, changes event classification, or changes basis; both sums cannot be substituted without reconciliation.',
           per_event_liability=str(per_event),single_endpoint_liability=str(contracted))
    record('7.3 attribution versus policy mutation','insufficiently specified',
           'Computing an attribution metric changes an analyst\'s information. No rule is supplied showing that it overwrites a physical risk matrix or enforces a tax floor. Legal classifications and policy effects are external assumptions, not consequences of the graph equations.')



# Run all validations; assertions signal failed checks, not contradicted claims.
def main():
    import argparse
    from collections import Counter
    parser = argparse.ArgumentParser(description='phase7 graph contraction and routing validation')
    parser.add_argument("--output", type=Path, help="Also save the JSON report to this path.")
    args = parser.parse_args()
    RESULTS.clear()
    validate_graph_mappings()
    validate_shift_matrix()
    validate_utility_indicator()
    validate_contraction_operator()
    validate_routing_objectives()
    validate_equivalence_and_consistency()
    report = dict(phase=7, python=platform.python_version(), scope="Synthetic mathematical validation; no legal findings.", conclusion="Phase 7 is not validated as a whole.", assessment_counts=dict(Counter(item["status"] for item in RESULTS)), results=RESULTS)
    payload = json.dumps(report, indent=2, allow_nan=False)
    if args.output:
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
