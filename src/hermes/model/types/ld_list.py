# SPDX-FileCopyrightText: 2025 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel
# SPDX-FileContributor: Michael Fritzsche

from collections import deque
from types import NotImplementedType
from .ld_container import (
    ld_container,
    JSON_LD_CONTEXT_DICT,
    EXPANDED_JSON_LD_VALUE,
    PYTHONIZED_LD_CONTAINER,
    JSON_LD_VALUE,
    TIME_TYPE,
    BASIC_TYPE,
)

from typing import Generator, Hashable, Union, Self, Any


class ld_list(ld_container):
    """
    An JSON-LD container resembling a list ("@set", "@list" or "@graph").
    See also :class:`ld_container`

    :ivar container_type: The type of JSON-LD container the list is representing. ("@set", "@list", "graph")
    :ivartype container_type: str
    :ivar item_list: The list of items (in expanded JSON-LD form) that are contained in this ld_list.
    :ivartype item_list: EXPANDED_JSON_LD_VALUE
    """

    def __init__(
        self: Self,
        data: Union[list[str], list[dict[str, EXPANDED_JSON_LD_VALUE]]],
        *,
        parent: Union["ld_container", None] = None,
        key: Union[str, None] = None,
        index: Union[int, None] = None,
        context: Union[list[Union[str, JSON_LD_CONTEXT_DICT]], None] = None,
    ) -> None:
        """
        Create a new ld_list container.

        :param self: The instance of ld_list to be initialized.
        :type self: Self
        :param data: The expanded json-ld data that is mapped (must be valid for @set, @list or @graph)
        :type data: list[str] | list[dict[str, BASIC_TYPE | EXPANDED_JSON_LD_VALUE]]
        :param parent: parent node of this container.
        :type parent: ld_container | None
        :param key: key into the parent container.
        :type key: str | None
        :param index: index into the parent container.
        :type index: int | None
        :param context: local context for this container.
        :type context: list[str | JSON_LD_CONTEXT_DICT] | None

        :return:
        :rtype: None

        :raises ValueError: bla
        :raises ValueError: bla
        """
        # check for validity of data
        if not isinstance(key, str):
            raise ValueError("The key is not a string or was omitted.")
        if not isinstance(data, list):
            raise ValueError("The given data does not represent an ld_list.")
        # infer the container type and item_list from data
        if self.is_ld_list(data):
            if "@list" in data[0]:
                self.container_type = "@list"
                self.item_list: list = data[0]["@list"]
            elif "@graph" in data[0]:
                self.container_type = "@graph"
                self.item_list: list = data[0]["@graph"]
            else:
                raise ValueError("The given @set is not fully expanded.")
        else:
            self.container_type = "@set"
            self.item_list: list = data
        # further validity checks
        if key == "@type":
            if any(not isinstance(item, str) for item in self.item_list) or self.container_type != "@set":
                raise ValueError("A given value for @type is not a string.")
        elif any(not isinstance(item, dict) for item in self.item_list):
            raise ValueError("A given value is not properly expanded.")
        # call super constructor
        super().__init__(data, parent=parent, key=key, index=index, context=context)

    def __getitem__(
        self: Self, index: Union[int, slice]
    ) -> Union[BASIC_TYPE, TIME_TYPE, ld_container, list[Union[BASIC_TYPE, TIME_TYPE, ld_container]]]:
        """
        Get the item(s) at position index in a pythonized form.

        :param self: The ld_list the items are taken from.
        :type self: Self
        :param index: The positon(s) from which the item(s) is/ are taken.
        :type index: int | slice

        :return: The pythonized item(s) at index.
        :rtype: BASIC_TYPE | TIME_TYPE | ld_container | list[BASIC_TYPE | TIME_TYPE | ld_container]]
        """
        # handle slices by applying them to a list of indices and then getting the items at those
        if isinstance(index, slice):
            return [self[i] for i in [*range(len(self))][index]]

        # get the item from the item_list and pythonize it. If necessary add the index.
        item = self._to_python(self.key, self.item_list[index])
        if isinstance(item, ld_container):
            item.index = index
        return item

    def __setitem__(
        self: Self, index: Union[int, slice], value: Union[JSON_LD_VALUE, BASIC_TYPE, TIME_TYPE, ld_container]
    ) -> None:
        """
        Set the item(s) at position index to the given value(s).
        All given values are expanded. If any are assimilated by self all items that would be added by this are added.

        :param self: The ld_list the items are set in.
        :type self: Self
        :param index: The positon(s) at which the item(s) is/ are set.
        :type index: int | slice
        :param value: The new value(s).
        :type value: Union[JSON_LD_VALUE, BASIC_TYPE, TIME_TYPE, ld_container]

        :return:
        :rtype: None
        """
        if not isinstance(index, slice):
            # expand the value
            value = self._to_expanded_json([value])
            # the returned value is always a list but my contain more then one item
            # therefor a slice on the item_list is used to add the expanded value(s)
            if index != -1:
                self.item_list[index:index+1] = value
            else:
                self.item_list[index:] = value
            return
        # check if the given values can be iterated (value does not have to be a list)
        try:
            iter(value)
        except TypeError as exc:
            raise TypeError("must assign iterable to extended slice") from exc
        # expand the values and merge all expanded values into one list
        expanded_value = ld_container.merge_to_list(*[self._to_expanded_json([val]) for val in value])
        # set the values at index to the expanded values
        self.item_list[index] = [val[0] if isinstance(val, list) else val for val in expanded_value]

    def __delitem__(self: Self, index: Union[int, slice]) -> None:
        """
        Delete the item(s) at position index.
        Note that if a deleted object is represented by an ld_container druing this process it will still exist
        and not be modified afterwards.

        :param self: The ld_list the items are deleted from.
        :type self: Self
        :param index: The positon(s) at which the item(s) is/ are deleted.
        :type index: int | slice

        :return:
        :rtype: None
        """
        del self.item_list[index]

    def __len__(self: Self) -> int:
        """
        Returns the number of items in this ld_list.

        :param self: The ld_list whose length is to be returned.
        :type self: Self

        :return: The length of self.
        :rtype: int
        """
        return len(self.item_list)

    def __iter__(self: Self) -> Generator[Union[BASIC_TYPE | TIME_TYPE | ld_container], None, None]:
        """
        Returns an iterator over the pythonized values contained in self.

        :param self: The ld_list over whose items is iterated.
        :type self: Self

        :return: The Iterator over self's values.
        :rtype: Generator[Union[BASIC_TYPE | TIME_TYPE | ld_container], None, None]
        """
        # return an Iterator over each value in self in its pythonized from
        for index, value in enumerate(self.item_list):
            item = self._to_python(self.key, value)
            # add which entry an ld_container is stored at, if item is an ld_container
            if isinstance(item, ld_container):
                item.index = index
            yield item

    def __contains__(self: Self, value: JSON_LD_VALUE) -> bool:
        """
        Returns whether or not value is contained in self.
        Note that it is not directly checked if value is in self.item_list.
        First value is expanded then it is checked if value is in self.item_list.
        If however value is assimilated by self it is checked if all values are contained in self.item_list.
        Also note that the checks whether the expanded value is in self.item_list is based on ld_list.__eq__.
        That means that this value is 'contained' in self.item_list if any object in self.item_list
        has the same @id like it or it xor the object in the item_list has an id an all other values are the same.

        :param self: The ld_list that is checked if it contains value.
        :type self: Self
        :param value: The object being checked whether or not it is in self.
        :type value: JSON_LD_VALUE

        :return: Whether or not value is being considered to be contained in self.
        :rtype: bool
        """
        # expand value
        expanded_value = self._to_expanded_json([value])
        # empty list -> no value to check
        if len(expanded_value) == 0:
            return True
        # call contains on all items in the expanded list if it contains more then one item
        # and return true only if all calls return true
        if len(expanded_value) > 1:
            return all(val in self for val in expanded_value)
        self_attributes = {"parent": self.parent, "key": self.key, "index": self.index, "context": self.full_context}
        # create a temporary list containing the expanded value
        # check for equality with a list containg exactly one item from self.item_list for every item in self.item_list
        # return true if for any item in self.item_list this check returns true
        if self.container_type == "@set":
            temp_list = ld_list(expanded_value, **self_attributes)
            return any(temp_list == ld_list([val], **self_attributes) for val in self.item_list)
        temp_list = ld_list([{self.container_type: expanded_value}], **self_attributes)
        return any(temp_list == ld_list([{self.container_type: [val]}], **self_attributes) for val in self.item_list)

    def __eq__(
        self: Self,
        other: Union[
            "ld_list",
            list[Union[JSON_LD_VALUE, BASIC_TYPE, TIME_TYPE, ld_container]],
            dict[str, list[Union[JSON_LD_VALUE, BASIC_TYPE, TIME_TYPE, ld_container]]],
        ],
    ) -> Union[bool, NotImplementedType]:
        """
        Returns wheter or not self is considered to be equal to other.<br>
        If other is not an ld_list, it is converted first.
        For each index it is checked if the ids of the items at index in self and other match if both have one,
        if only one has or neither have an id all other values are compared.<br>
        Note that due to those circumstances equality is not transitve
        meaning if a == b and b == c is is not guaranteed that a == c.<br>
        If self or other is considered unordered the comparison is more difficult. All items in self are compared
        with all items in other. On the resulting graph given by the realtion == the Hopcroft-Karp algoritm is used
        to determine if there exists a bijection reordering self so that the ordered comparison of self with other
        returns true.

        :param self: The ld_list other is compared to.
        :type self: Self
        :param other: The list/ container/ ld_list self is compared to.
        :type other: ld_list | list[JSON_LD_VALUE | BASIC_TYPE | TIME_TYPE | ld_container]
            | dict[str, list[JSON_LD_VALUE | BASIC_TYPE | TIME_TYPE | ld_container]]

        :return: Whether or not self and other are considered equal.
            If other is of the wrong type return NotImplemented instead.
        :rtype: bool | NotImplementedType
        """
        # check if other has an acceptable type
        if not (isinstance(other, (list, ld_list)) or ld_list.is_container(other)):
            return NotImplemented

        # convert other into an ld_list if it isn't one already
        if isinstance(other, dict):
            other = [other]
        if isinstance(other, list):
            if ld_list.is_ld_list(other):
                other = ld_list.get_item_list_from_container(other[0])
            other = self.from_list(other, parent=self.parent, key=self.key, context=self.context)

        # check if the length matches
        if len(self.item_list) != len(other.item_list):
            return False

        # check for special case (= key is @type)
        if (self.key == "@type") ^ (other.key == "@type"):
            return False
        if self.key == other.key == "@type":
            # lists will only contain string
            return self.item_list == other.item_list

        if self.container_type == other.container_type == "@list":
            # check if at each index the items are considered equal
            for index, (item, other_item) in enumerate(zip(self.item_list, other.item_list)):
                # check if items are values
                if ((ld_container.is_typed_json_value(item) or ld_container.is_json_value(item)) and
                        (ld_container.is_typed_json_value(other_item) or ld_container.is_json_value(other_item))):
                    if not ld_container.are_values_equal(item, other_item):
                        return False
                    continue
                # check if both contain an id and compare
                if "@id" in item and "@id" in other_item:
                    if item["@id"] != other_item["@id"]:
                        return False
                    continue
                # get the 'real' items (i.e. can also be ld_dicts or ld_lists)
                item = self[index]
                other_item = other[index]
                # compare using the correct equals method
                res = item.__eq__(other_item)
                if res == NotImplemented:
                    # swap order if first try returned NotImplemented
                    res = other_item.__eq__(item)
                # return false if the second comparison also fails or one of them returned false
                if res is False or res == NotImplemented:
                    return False
            # return true because no unequal elements where found
            return True
        else:
            # check which items in self are equal the which in other
            equality_pairs = [[] for i in range(len(self))]  # j in equality_pairs[i] <=> self[i] == other[j]
            for index, item in enumerate(self.item_list):
                for other_index, other_item in enumerate(other.item_list):
                    # check if items are values
                    if ((ld_container.is_typed_json_value(item) or ld_container.is_json_value(item)) and
                            (ld_container.is_typed_json_value(other_item) or ld_container.is_json_value(other_item))):
                        if ld_container.are_values_equal(item, other_item):
                            equality_pairs[index] += [other_index]
                        continue
                    # check if both contain an id and compare
                    if "@id" in item and "@id" in other_item:
                        if item["@id"] == other_item["@id"]:
                            equality_pairs[index] += [other_index]
                        continue
                    # get the 'real' items (i.e. can also be ld_dicts or ld_lists)
                    item = self[index]
                    other_item = other[index]
                    # compare using the correct equals method
                    res = item.__eq__(other_item)
                    if res == NotImplemented:
                        # swap order if first try returned NotImplemented
                        res = other_item.__eq__(item)
                    # if one of both comparisons returned true the elements are equal
                    if res:
                        equality_pairs[index] += [other_index]
                if len(equality_pairs[index]) == 0:
                    # there exists no element in other that is equal to item
                    return False
            # check if there is a way to chose one index from equality_pairs[i] for every i
            # so that there are no two i's with the same chosen index.
            # If such a way exists self and other are considered equal. If not they are considered to be not equal.
            # solved via a Hopcroft-Karp algorithm variant:
            # The bipartite graph is the disjoint union of the vertices 1 to len(self) and
            # freely chosen ids for each list in equality_pairs.
            # The graph has an edge from i to the id of a list if i is contained in the list.
            item_count = len(self)
            verticies_set1 = {*range(item_count)}
            verticies_set2 = {*range(item_count, 2 * item_count)}
            edges = {i: tuple(j for j in verticies_set2 if i in equality_pairs[j - item_count]) for i in verticies_set1}
            return ld_list._hopcroft_karp(verticies_set1, verticies_set2, edges) == len(self)

    @classmethod
    def _bfs_step(
        cls: Self, verticies1: set[Hashable], edges: dict[Hashable, tuple[Hashable]], matches: dict[Hashable, Hashable],
        distances: dict[Hashable, Union[int, float]]
    ) -> bool:
        """
        Completes the BFS step of Hopcroft-Karp. I.e.:<br>
        Finds the shortest path from all unmatched verticies in verticies1 to any unmatched vertex in any value in edges
        where the connecting paths are alternating between matches and its complement.<br>
        It also marks each vertex in verticies1 with how few verticies from verticies1 have to be passed
        to reach the vertex from an unmatched one in verticies1. This is stored in distances.

        :param verticies1: The set of verticies in the left partition of the bipartite graph.
        :type verticies1: set[Hashable]
        :param edges: The edges in the bipartite graph. (As the edges are bidirectional they are expected to be given in
            this format: Dictionary with keys being the vertices in the left partition and values being tuples
            of verticies in the right partition.)
        :type edges: dict[Hashable, tuple[Hashable]]
        :param matches: The current matching of verticies in the left partition with the ones in the right partition.
        :type matches: dict[Hashable, Hashable]
        :param distances: The reference to the dictionary mapping verticies of the left partition to the minimal
            number of verticies in the left partition that will be passed on a path from an unmatched vertex of the left
            partition to the vertex that is the key.
        :type distances: dict[Hashable, Union[int, float]]

        :returns: Wheter or not a alternating path from an unmatched vertex in the left partition to an unmatched vertex
            in the right partition exists.
        :rtype: bool
        """
        # initialize the queue and set the distances to zero for unmatched vertices and to inf for all others
        queue = deque()
        for ver in verticies1:
            if matches[ver] is None:
                distances[ver] = 0
                queue.append(ver)
            else:
                distances[ver] = float("inf")
        distances[None] = float("inf")
        # begin BFS
        while len(queue) != 0:
            ver1 = queue.popleft()
            # if the current vertex has a distance less then the current minimal one from an unmatched vertex in the
            # left partition to an unmatched one in the right partition
            if distances[ver1] < distances[None]:
                # iterate over all vertices in the right partition connected to ver1
                for ver2 in edges[ver1]:
                    # if the vertex ver2 is matched with (or None if not matched) wasn't visited yet
                    if distances[matches[ver2]] == float("inf"):
                        # initialize the distance and queue the vertex for further search
                        distances[matches[ver2]] = distances[ver1] + 1
                        queue.append(matches[ver2])
        # if a path to None i.e. an unmatched vertex in the right partition was found return true otherwise false
        return distances[None] != float("inf")

    @classmethod
    def _dfs_step(
        cls: Self, ver: Hashable, edges: dict[Hashable, tuple[Hashable]], matches: dict[Hashable, Hashable],
        distances: dict[Hashable, Union[int, float]]
    ) -> bool:
        """
        Completes the DFS step of Hopcroft-Karp. I.e.:<br>
        Adds all edges on every path with the minimal path length to matches if they would be in the symmetric
        difference of matches and the set of edges on the union of the paths.

        :param ver: The set of verticies in the left partition of the bipartite graph.
        :type vert: Hashable
        :param edges: The edges in the bipartite graph. (As the edges are bidirectional they are expected to be given in
            this format: Dictionary with keys being the vertices in the left partition and values being tuples
            of verticies in the right partition.)
        :type edges: dict[Hashable, tuple[Hashable]]
        :param matches: The current matching of verticies in the left partition with the ones in the right partition.
        :type matches: dict[Hashable, Hashable]
        :param distances: The reference to the dictionary mapping verticies of the left partition to the minimal
            number of verticies in the left partition that will be passed on a path from an unmatched vertex of the left
            partition to the vertex that is the key. The values will be replaced with float("inf") to mark already
            visited vertices.
        :type distances: dict[Hashable, Union[int, float]]

        :returns: Wheter or not a path from the unmatched vertex ver in the left partition to an unmatched vertex
            in the right partition could still exist.
        :rtype: bool
        """
        # recursion base case: None always has a shortest possible path to itself
        if ver is None:
            return True
        # iterate over all vertices connected to ver in the right partition
        for ver2 in edges[ver]:
            # if ver2 is on a path with minimal length and not all subtrees have been searched already
            if distances[matches[ver2]] == distances[ver] + 1:
                if cls._dfs_step(matches[ver], edges, matches, distances):
                    # add the edge to the matches and return true
                    matches[ver2] = ver
                    matches[ver] = ver2
                    return True
        # mark this vertex as completly searched
        distances[ver] = float("inf")
        return False

    @classmethod
    def _hopcroft_karp(
        cls: Self, verticies1: set[Hashable], verticies2: set[Hashable], edges: dict[Hashable, tuple[Hashable]]
    ) -> int:
        """
        Implementation of Hopcroft-Karp. I.e.:<br>
        Finds how maximal number of edges with the property that no two edges share an endpoint (and startpoint)
        in the given bipartite graph.<br>
        Note that verticies1 and verticies2 have to be disjoint.

        :param verticies1: The set of verticies in the left partition of the bipartite graph.
        :type verticies1: set[Hashable]
        :param verticies2: The set of verticies in the right partition of the bipartite graph.
        :type verticies2: set[Hashable]
        :param edges: The edges in the bipartite graph. (As the edges are bidirectional they are expected to be given in
            this format: Dictionary with keys being the vertices in the left partition and values being tuples
            of verticies in the right partition.)
        :type edges: dict[Hashable, tuple[Hashable]]

        :returns: The number of edges.
        :rtype: int
        """
        # initializes the first matching. None is a imaginary vertex to denote unmatched vertices.
        matches = dict()
        for ver in verticies1:
            matches[ver] = None
        for ver in verticies2:
            matches[ver] = None
        matching_size = 0
        distances = dict()
        while cls._bfs_step(verticies1, edges, matches, distances):
            # while a alternating path from an unmatched vertex in the left partition exits
            # recalculate the distances and
            # iterate over all unmatched vertices in the left partition.
            for ver in verticies1:
                if matches[ver] is None:
                    # create the new matches dict and if a new edge was added increase the size of the matching
                    if cls._dfs_step(ver, edges, matches, distances):
                        matching_size += 1
        # return the size of the matching
        return matching_size

    def __ne__(
        self: Self,
        other: Union[
            "ld_list",
            list[Union[JSON_LD_VALUE, BASIC_TYPE, TIME_TYPE, ld_container]],
            dict[str, list[Union[JSON_LD_VALUE, BASIC_TYPE, TIME_TYPE, ld_container]]],
        ],
    ) -> Union[bool, NotImplementedType]:
        """
        Returns whether or not self and other not considered to be equal.
        (Returns not self.__eq__(other) if the return type is bool.
        See ld_list.__eq__ for more details on the comparison.)

        :param self: The ld_list other is compared to.
        :type self: Self
        :param other: The list/ container/ ld_list self is compared to.
        :type other: ld_list | list[JSON_LD_VALUE | BASIC_TYPE | TIME_TYPE | ld_container]
            | dict[str, list[JSON_LD_VALUE | BASIC_TYPE | TIME_TYPE | ld_container]]

        :return: Whether or not self and other are not considered equal.
            If other is of the wrong type return NotImplemented instead.
        :rtype: bool | NotImplementedType
        """
        # compare self and other using __eq__
        x = self.__eq__(other)
        # return NotImplemented if __eq__ did so and else the inverted result of __eq__
        if x is NotImplemented:
            return NotImplemented
        return not x

    def append(self: Self, value: Union[JSON_LD_VALUE, BASIC_TYPE, TIME_TYPE, ld_container]) -> None:
        """
        Append the item to the given ld_list self.
        The given value is expanded. If it is assimilated by self all items that would be added by this are added.

        :param self: The ld_list the item is appended to.
        :type self: Self
        :param value: The new value.
        :type value: Union[JSON_LD_VALUE, BASIC_TYPE, TIME_TYPE, ld_container]

        :return:
        :rtype: None
        """
        self.item_list.extend(self._to_expanded_json([value]))

    def extend(self: Self, value: list[Union[JSON_LD_VALUE, BASIC_TYPE, TIME_TYPE, ld_container]]) -> None:
        """
        Append the items in value to the given ld_list self.
        The given values are expanded. If any are assimilated by self all items that would be added by this are added.

        :param self: The ld_list the items are appended to.
        :type self: Self
        :param value: The new values.
        :type value: list[Union[JSON_LD_VALUE, BASIC_TYPE, TIME_TYPE, ld_container]]

        :return:
        :rtype: None
        """
        for item in value:
            self.append(item)

    def to_python(self: Self) -> list[PYTHONIZED_LD_CONTAINER]:
        """
        Return a fully pythonized version of this object where all ld_container are replaced by lists and dicts.

        :param self: The ld_list whose fully pythonized version is returned.
        :type self: Self

        :return: The fully pythonized version of self.
        :rtype: list[PYTHONIZED_LD_CONTAINER]
        """
        return [
            item.to_python() if isinstance(item, ld_container) else item
            for item in self
        ]

    @classmethod
    def is_ld_list(cls: type[Self], ld_value: Any) -> bool:
        """
        Returns wheter the given value is considered to be possible of representing an ld_list.<br>
        I.e. if ld_value is of the form [{container_type: [...]}] where container_type is '@set', '@list' or '@graph'.

        :param ld_value: The value that is checked.
        :type ld_value: Any

        :returns: Wheter or not ld_value could represent an ld_list.
        :rtype: bool
        """
        return cls.is_ld_node(ld_value) and cls.is_container(ld_value[0])

    @classmethod
    def is_container(cls: type[Self], value: Any) -> bool:
        """
        Returns wheter the given value is considered to be possible of representing an json-ld container.<br>
        I.e. if ld_value is of the form {container_type: [...]} where container_type is '@set', '@list' or '@graph'.

        :param ld_value: The value that is checked.
        :type ld_value: Any

        :returns: Wheter or not ld_value could represent a json-ld container.
        :rtype: bool
        """
        return (
            isinstance(value, dict)
            and [*value.keys()] in [["@list"], ["@set"], ["@graph"]]
            and any(isinstance(value.get(cont, None), list) for cont in {"@list", "@set", "@graph"})
        )

    @classmethod
    def from_list(
        cls: type[Self],
        value: list[Union[JSON_LD_VALUE, BASIC_TYPE, TIME_TYPE]],
        *,
        parent: Union[ld_container, None] = None,
        key: Union[str, None] = None,
        context: Union[str, JSON_LD_CONTEXT_DICT, list[Union[str, JSON_LD_CONTEXT_DICT]], None] = None,
        container_type: str = "@set"
    ) -> "ld_list":
        """
        Creates a ld_list from the given list with the given parent, key, context and container_type.<br>
        Note that only container_type '@set' is valid for key '@type'.<br>
        Further more note that if parent would assimilate the values in value no new ld_list is created
        and the given values are appended to parent instead and parent is returned.

        :param value: The list of values the ld_list should be created from.
        :type value: list[JSON_LD_VALUE | BASIC_TYPE | TIME_TYPE]
        :param parent: The parent container of the new ld_list.<br>If value is assimilated by parent druing JSON-LD
            expansion parent is extended by value and parent is returned.
        :type parent: ls_container | None
        :param key: The key into the inner most parent container representing a dict of the new ld_list.
        :type: key: str | None
        :param context: The context for the new list (is will also inherit the context of parent).<br>
            Note that this context won't be added to parent if value is assimilated by parent and parent is returned.
        :type context: str | JSON_LD_CONTEXT_DICT | list[str | JSON_LD_CONTEXT_DICT] | None
        :param container_type: The container type of the new list valid are '@set', '@list' and '@graph'.<br>
            If value is assimilated by parent and parent is returned the given container_type won't affect
            the container type of parent.<br> Also note that only '@set' is valid if key is '@type'.
        :type container_type: str

        :return: The new ld_list build from value or if value is assimilated by parent, parent extended by value.
        :rtype: ld_list

        :raises ValueError: If key is '@type' and container_type is not '@set'.
        """
        # TODO: handle context if not of type list or None
        # validate container_type
        if key == "@type":
            if container_type != "@set":
                raise ValueError(f"The given container type is {container_type} which is invalid for a list"
                                 " containing values for '@type' (valid is only '@set').")
        if container_type in {"@list", "@graph"}:
            # construct json-ld container that indicates the container type
            value = [{container_type: value}]
        elif container_type != "@set":
            raise ValueError(f"Invalid container type: {container_type}. (valid are only '@set', '@list' and '@graph')")

        if parent is not None:
            # expand value in the "context" of parent
            if isinstance(parent, ld_list):
                expanded_value = parent._to_expanded_json([value])
                if (len(expanded_value) != 1 or
                        not (isinstance(expanded_value[0], list) or cls.is_container(expanded_value[0]))):
                    # parent assimilated value druing expansion. Therefor the values are appended and parent returned
                    # if value is assimilated but contained only one list after expansion this list is used for
                    # the new list instead of expanding parent
                    parent.extend(expanded_value)
                    return parent
            else:
                expanded_value = parent._to_expanded_json({key: value})[cls.ld_proc.expand_iri(parent.active_ctx, key)]
        else:
            # create a temporary ld_list which is necessary for expansion
            # value is not passed in a list as usual because value should be treated like the item list of the
            # temporary object and not like a item in it
            expanded_value = cls([], parent=None, key=key, context=context)._to_expanded_json(value)

        # construct and return the final ld_list from the expanded_value
        return cls(expanded_value, parent=parent, key=key, context=context)

    @classmethod
    def get_item_list_from_container(cls: type[Self], ld_value: dict[str, list[Any]]) -> list[Any]:
        """
        Returns the item list from a container, the given ld_value, (i.e. {container_type: item_list}).<br>
        Only '@set', '@list' and '@graph' are valid container types.

        :param ld_value: The container whose item list is to be returned.
        :type ld_value: dict[str, list[Any]]

        :returns: The list the container holds.
        :rtype: list[Any]

        :raises ValueError: If the item_container is not a dict.
        :raises ValueError: If the container_type is not exactly one of '@set', '@list' and '@graph'.
        :raises ValueError: If the item_list is no list.
        """
        if type(ld_value) != dict:
            raise ValueError(f"The given data {ld_value} is not a dictionary and therefor no container.")
        if len(ld_value.keys()) != 1:
            raise ValueError(f"The given data contains two many or few entries ({len(ld_value.keys())})."
                             " It should be only one entry: '@set', '@list' or '@graph' as key and a list as value.")
        # find the container type to return the item_list
        for cont in {"@list", "@set", "@graph"}:
            if cont in ld_value:
                if type(ld_value[cont]) != list:
                    raise ValueError(f"The item list of {ld_value} is of type {type(ld_value[cont])} and not list.")
                return ld_value[cont]
        raise ValueError(f"The given data {ld_value} does not represent a container.")
