import unreal
names=[n for n in dir(unreal) if any(k in n.lower() for k in ['animgraph','animblueprint','copy','pose','graphnode','k2node'])]
print('\n'.join(names))
