"""Types for representing practice problems.

When practice problems are parsed from their on-disk representations, they are
read into the abstract types defined in this module by the parsers in
`practicebank.parsers`. The problems are then converted into HTML and other
output formats by the renderers in `practicebank.renderers`. Therefore, these
types are intermediate representations decoupling the parsers from the
renderers.

"""

from abc import ABC, abstractmethod
import typing

from .exceptions import IllegalChild


class InternalNode(ABC):
    """Abstract base class for nodes in the practice problem tree."""

    allowed_child_types = tuple()
    attrs = tuple()

    def __init__(self, *, children=None):
        self._children = []
        if children is not None:
            for child in children:
                self.add_child(child)

    def add_child(self, node: typing.Union["InternalNode", "LeafNode"]):
        """Add a child node, checking to see if it's a valid type."""
        if not isinstance(node, self.allowed_child_types):
            raise IllegalChild(self, node)
        self._children.append(node)

    def children(self) -> typing.Iterator[typing.Union["InternalNode", "LeafNode"]]:
        """Iterator over the child nodes."""
        return iter(self._children)

    def number_of_children(self):
        return len(self._children)

    def _attributes_equal(self, other):
        return all(getattr(self, attr) == getattr(other, attr) for attr in self.attrs)

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False

        if len(self._children) != len(other._children):
            return False

        child_pairs = zip(self._children, other._children)

        return self._attributes_equal(other) and all(x == y for x, y in child_pairs)

    def __repr__(self):
        return f"{type(self).__name__}({self._children!r})"


class LeafNode(ABC):
    """Abstract base class for leaf nodes in the practice problem tree."""

    attrs = tuple()

    def _attributes_equal(self, other):
        return all(getattr(self, attr) == getattr(other, attr) for attr in self.attrs)

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False

        return self._attributes_equal(other)

    def __repr__(self):
        return f"{type(self).__name__}({self.__dict__!r})"


class Problem(InternalNode):
    """A practice problem."""


class Subproblem(InternalNode):
    """A subproblem within a problem."""


class Paragraph(InternalNode):
    """A paragraph of text."""


class TextNode(LeafNode, ABC):
    """Abstract base class for text nodes."""

    attrs = ("text",)

    def __init__(self, text):
        super().__init__()
        self.text = text


class NormalText(TextNode):
    """Text with no formatting."""


class BoldText(TextNode):
    """Text that should be bolded."""


class ItalicText(TextNode):
    """Text that should be italicized."""


class DisplayMath(LeafNode):
    """A block of text that should be typeset as display math."""

    attrs = ("latex",)

    def __init__(self, latex: str):
        super().__init__()
        self.latex = latex


class InlineMath(LeafNode):
    """A block of text that should be typeset as inline math."""

    attrs = ("latex",)

    def __init__(self, latex: str):
        super().__init__()
        self.latex = latex


class Code(LeafNode):
    """A block of code."""

    attrs = ("language", "code")

    def __init__(self, language: str, code: str):
        super().__init__()
        self.language = language
        self.code = code


class InlineCode(LeafNode):
    """A block of code, displayed inline."""

    attrs = ("language", "code")

    def __init__(self, language: str, code: str):
        super().__init__()
        self.language = language
        self.code = code


class Image(LeafNode):
    """An image.

    Attributes
    ----------
    relative_path : str
        The path to the image relative to the problem's directory.
    data : bytes
        The image data.

    """

    attrs = ("relative_path", "data")

    def __init__(self, relative_path: str, data: bytes):
        super().__init__()
        self.relative_path = relative_path
        self.data = data


class MultipleChoices(InternalNode):
    """A multiple choice area. Container of Choices"""


class MultipleSelect(InternalNode):
    """A select-all-that-apply area in a question. Container of Choices"""


class Choice(InternalNode):
    """A choice within a multiple choice question."""

    attrs = ("correct",)

    def __init__(self, *, correct=False, children=None):
        super().__init__(children=children)
        self.correct = correct


class TrueFalse(LeafNode):
    """A true/false question."""

    attrs = ("solution",)

    def __init__(self, solution: bool):
        super().__init__()
        self.solution = solution


class FillInTheBlank(InternalNode):
    """A fill-in-the-blank question."""


class Solution(InternalNode):
    """A solution to a problem."""


Problem.allowed_child_types = (
    Subproblem,
    Code,
    DisplayMath,
    Image,
    MultipleChoices,
    MultipleSelect,
    TrueFalse,
    FillInTheBlank,
    Solution,
    NormalText,
    BoldText,
    ItalicText,
    InlineMath,
    InlineCode,
    Paragraph,
)

Paragraph.allowed_child_types = (
    NormalText,
    BoldText,
    ItalicText,
    InlineMath,
    InlineCode,
)

# do not allow subproblems to contain subproblems
Subproblem.allowed_child_types = Problem.allowed_child_types[1:]

MultipleChoices.allowed_child_types = (Choice,)

MultipleSelect.allowed_child_types = (Choice,)

Choice.allowed_child_types = (
    NormalText,
    BoldText,
    ItalicText,
    InlineMath,
    DisplayMath,
    Code,
    InlineCode,
    Image,
    Paragraph,
)

Solution.allowed_child_types = Choice.allowed_child_types
FillInTheBlank.allowed_child_types = Choice.allowed_child_types
