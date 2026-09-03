def BalanceChances(arr,val):
    sum = val
    for a in arr:
        sum = sum +a
    if sum == 100:
        return arr
    dif = 100-sum
    while(dif != 0):
        divider = 0
        rest = 0
        for i in range(len(arr)):
            if arr[i] != 0:
                divider = divider + 1
        for i in range(len(arr)):
            if arr[i] != 0:
                arr[i] = arr[i]+dif/divider
                if arr[i]<0:
                    rest = rest + arr[i]
                    arr[i] = 0
        dif = rest
    return arr