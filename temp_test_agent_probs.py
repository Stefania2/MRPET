from app import ExternalAgent, run_simulation

agents = ['A', 'B', 'C']
params = [(10,0.01,0.5),(1000,0.5,0.7),(100000,0.9,0.95)]
for name,(mass,vel,coh) in zip(agents,params):
    agent = ExternalAgent(name, 0, mass, vel, coh)
    res = run_simulation(agent, 11, 5)
    print('Agent', name, 'mass', mass, 'vel', vel, 'coh', coh)
    for branch in res.future_branches:
        print('  ', branch)
    print('full probs', [f"{item['event']}={item['probability']*100:.2f}%" for item in res.event_probabilities])
    print()
