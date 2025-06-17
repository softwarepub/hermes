from hermes.model.types import ld_list


class MergeError(ValueError):
    pass


class MergeAction:
    def merge(self, target, key, value, update):
        raise NotImplementedError()


class Reject(MergeAction):
    @classmethod
    def merge(cls, target, key, value, update):
        if value != update:
            target.reject(key, update)
        return value


class Replace(MergeAction):
    @classmethod
    def merge(cls, target, key, value, update):
        if value != update:
            target.replace(key, value)
        return update


class Concat(MergeAction):
    @classmethod
    def merge(cls, target, key, value, update):
        return cls.merge_to_list(value, update)

    @classmethod
    def merge_to_list(cls, head, tail):
        if not isinstance(head, (list, ld_list)):
            head = [head]
        if not isinstance(tail, (list, ld_list)):
            head.append(tail)
        else:
            head.extend(tail)
        return head


class Collect(MergeAction):
    def __init__(self, match):
        self.match = match

    def merge(self, target, key, value, update):
        if not isinstance(value, list):
            value = [value]
        if not isinstance(update, list):
            update = [update]

        for update_item in update:
            if not any(self.match(item, update_item) for item in value):
                value.append(update_item)

        if len(value) == 1:
            return value[0]
        else:
            return value


class MergeSet(MergeAction):
    def __init__(self, match, merge_items=True):
        self.match = match
        self.merge_items = merge_items

    def merge(self, target, key, value, update):
        for item in update:
            target_item = target.match(key[-1], item, self.match)
            if target_item and self.merge_items:
                target_item.update(item)
            else:
                value.append(item)
        return value
