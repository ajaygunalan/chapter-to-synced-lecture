# Code on slides: house style

Code supports the chapter's lesson. Preserve the book's example, algorithmic
structure, and names so the conceptual diagram, worked state, listing, and
source text remain recognizable as the same case. Modernize syntax or
translate to the listener's preferred language only when that makes the
mechanism clearer without introducing distracting new machinery. Cite the
book's listing by page and identify meaningful adaptations.

**Show the code that establishes the mechanism.** A conceptual frame need not
contain a whole algorithm or `main`; use a focused listing or block when that
is enough. After the plain definition, start with a toy that isolates the new
feature; do not combine the entire chapter's machinery just to make it short.
Then map that behavior into the book's worked listing. Introduce unfamiliar
syntax and helpers before revealing a block that depends on them; build the
implementation in meaningful steps tied to the concept. A complete listing
can consolidate those steps.
A detailed walkthrough shows its input, relevant steps, and result.
A code-dependent question includes all relevant code and input immediately
above the choices, without requiring another frame for missing context. Check
computed outputs against a real run. Where a run's tie-breaks differ from the
book's figure, explain the difference.

Use the learner's demonstrated knowledge to choose syntax refreshers. Someone
who understands callable objects may still have forgotten constructor member
initialization or template type parameters. Explain the unfamiliar construct
with ordinary names and a small isolated use before combining it with return
deduction, capture, or forwarding. Do not repeat the understood object model
or turn the refresher into a multi-feature diagnostic. Explain what a type
placeholder, parameter, or initializer denotes before describing its effect
inside a generic listing.

**Connect the code to its concept and state.** During a walkthrough, highlight
the relevant code line or block and corresponding diagram or graph element
as the voice explains their relationship. Advance the worked state at a
meaningful step. Use the same names and consistent semantic colors across
views. Shift focus or split frames to keep each pairing readable; a permanent
dense overview-plus-code-plus-state layout is not required. Walkthroughs are
valuable evidence for the lesson, not a requirement to narrate every line.

For newly written supporting code, use this concise style where compatible
with the source example and the learner's understanding. Readability and
necessary explanatory comments take priority over packing a slide. Preserve
names and structures needed to recognize the book's listing rather than
renaming them just to satisfy house style:

- 4-space indent, K&R braces (`{` on the same line), `for(`/`if(`/`while(`
  with no space before the paren, packed loop headers
  (`for(int i = 0; i < n; i++)`), spaces around `=` `==` `&&` `||`
- retain braces and line breaks when they clarify scope or control flow;
  compact forms such as `if(!node) return;` are fine when already familiar
- camelCase; `i j r c` for indices, `n m rows cols` for sizes; the answer is
  `result`; helpers named for what they do (`dfs`, `backtrack`)
- for C++ adaptations, range-for and structured bindings when they clarify
  the original operation; avoid adding unfamiliar APIs solely to modernize
  the source example
- state that several helpers share lives in members, `private:` first
- `//` comments near the relevant line explain an unfamiliar construct's
  role, a type transformation, an invariant, or its job in the diagram;
  omit restatements of syntax the learner already understands
- whitespace between phases, not between every line
- no `#include` lines and no `using namespace`: a slide shows the algorithm,
  not the file; the headers are implied by the names (`std::vector`,
  `std::println`)
- lines short enough to sit beside a picture — about 55 characters

When an existing C++23 listing uses `<print>`:
[GCC 13](https://gcc.gnu.org/gcc-13/) ships no `<print>`; build with a shim
(`-include println_shim.h` defining `std::println` over `std::format`) so the
listing itself stays real C++23.
