# Minimal test for TD 2025.32460 operator creation
# Run in TD Textport

me = op('/project1')
print('Root:', me)

# Test 1: create with name
try:
    x = me.create(baseCOMP, 'test_container_1')
    print('Test 1 OK (with name):', x)
except Exception as e:
    print('Test 1 FAIL:', e)

# Test 2: create without name
try:
    x = me.create(baseCOMP)
    print('Test 2 OK (no name):', x)
except Exception as e:
    print('Test 2 FAIL:', e)

# Test 3: CHOP creation
try:
    c = me.create(nullCHOP, 'test_chop_1')
    print('Test 3 OK (CHOP with name):', c)
except Exception as e:
    print('Test 3 FAIL:', e)

# Test 4: CHOP without name
try:
    c = me.create(nullCHOP)
    print('Test 4 OK (CHOP no name):', c)
except Exception as e:
    print('Test 4 FAIL:', e)

# Clean up
for child in me.findChildren(name='test_*'):
    child.destroy()
print('Cleanup done.')
