from collections import defaultdict
from io import BytesIO
from itertools import chain
from typing import Dict, IO, Iterator, List, Union

import attr

from sortedcontainers import SortedKeyList

from cassis.typesystem import Annotation


@attr.s(slots=True)
class Sofa():
    sofaNum: int = attr.ib()
    xmiID: int = attr.ib(default=None)
    sofaID: str = attr.ib(default=None)
    sofaString: str = attr.ib(default=None)
    mimeType: str = attr.ib(default=None)


@attr.s(slots=True)
class View():
    sofa: int = attr.ib()
    members: List[int] = attr.ib()

class Cas():

    def __init__(self, annotations: List[Annotation] = None, namespaces: Dict[str, str] = None,
                 sofas: List[Sofa] = None, views: List[View] = None):
        self.namespaces = namespaces or {}
        self._sofas = {}
        self.views = views or []
        # Annotations are sorted by begin index first (smaller first). If begin
        #  is equal, sort by end index, smaller first. This is the same as
        # comparing a Python tuple of (begin, end)
        self._annotations = defaultdict(lambda: SortedKeyList(key=lambda a: (a.begin, a.end)))
        _annotations = annotations or []
        for annotation in _annotations:
            self._annotations[annotation.type].add(annotation)

        # Handle sofas
        if sofas == None or len(sofas) == 0:
            _sofas = [Sofa(sofaNum=1)]
        else:
            _sofas = sofas

        for sofa in _sofas:
            self._sofas[sofa.sofaNum] = sofa

        # Find maximum id
        maximum_xmiID = 1
        for obj in chain(_sofas, _annotations):
            if obj.xmiID and obj.xmiID > maximum_xmiID:
                maximum_xmiID = obj.xmiID

        self.maximum_xmiID = maximum_xmiID

    def add_annotation(self, annotation: Annotation):
        """ Adds an annotation to this Cas

        Args:
            annotation: The annotation to add
        """
        if annotation.xmiID is None:
            annotation.xmiID = self._get_next_id()

        self._annotations[annotation.type].add(annotation)

    def get_covered_text(self, annotation: Annotation) -> str:
        """ Gets the text that is covered by `annotation`

        Args:
            annotation:

        Returns:

        """
        sofa = self.get_sofa(annotation.sofa)
        return sofa.sofaString[annotation.begin:annotation.end]

    def select(self, typename: str) -> Iterator[Annotation]:
        for annotation in self._annotations[typename]:
            yield annotation

    def select_covered(self, typename: str, covering_annotation: Annotation) -> Iterator[Annotation]:
        """ Returns an iterator over covered annotations

        Return all annotations that are covered

        Only returns annotations that are fully covered, overlapping annotations
        are ignored.

        Args:
            typename: The type name of the annotations to be returned
            covering_annotation: The name of the annotation which covers

        Returns:
            an iterator over covered annotations
        """
        c_begin = covering_annotation.begin
        c_end = covering_annotation.end

        annotations = self._annotations[typename]

        # The entry point is the index of the first annotation whose `begin`
        # is equal or higher than the `begin` of the covering annotation
        entry_point = annotations.bisect_key_left((c_begin, c_begin))

        for annotation in annotations[entry_point:]:
            if annotation.begin >= c_begin and annotation.end <= c_end:
                yield annotation

            if annotation.begin > c_end:
                break

    def select_all(self) -> Iterator[Annotation]:
        """ Returns an iterator over all annotations in this Cas

        Returns:
            an iterator over all annotations in this Cas
        """
        for annotations in self._annotations.values():
            for annotation in annotations:
                yield annotation

    def get_sofa(self, sofa_id: int) -> Sofa:
        return self._sofas[sofa_id]

    @property
    def sofas(self) -> List[Sofa]:
        return list(self._sofas.values())

    def _get_next_id(self):
        self.maximum_xmiID += 1
        return self.maximum_xmiID

    def to_xmi(self, path_or_buf: Union[IO, str] = None):
        """ Creates a string representation of this type system

        Args:
            path_or_buf: File path or file-like object, if None is provided the result is returned as a string.

        Returns:

        """
        from cassis.xmi import CasXmiSerializer

        serializer = CasXmiSerializer()

        # If `path_or_buf` is None, then serialize to a string and return it
        if path_or_buf is None:
            sink = BytesIO()
            serializer.serialize(sink, self)
            return sink.getvalue().decode('utf-8')
        else:
            serializer.serialize(path_or_buf, self)
