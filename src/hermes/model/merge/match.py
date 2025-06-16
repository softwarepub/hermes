def match_equals(a, b):
    return a == b


def match_keys(*keys):
    def match_func(left, right):
        active_keys = [key for key in keys if key in left and key in right]
        pairs = [(left[key] == right[key]) for key in active_keys]
        return len(active_keys) > 0 and all(pairs)
    return match_func
