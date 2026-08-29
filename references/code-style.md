# Code on slides: house style

Code the lecture shows is **C++23**, whatever language the book prints. The
listener writes C++; a listing in a language they don't read teaches them the
language, not the algorithm. The algorithm, its structure and the names that
matter stay the book's, so the two can be put side by side; the book's listing
is cited by page and the voice says the rewrite is the lecture's ("the book
prints this in C on page 194 — here it is written for today").

**A whole algorithm comes with a `main`**: the input built from the chapter's
own example, the call, the output printed. The listener must know what goes in
and what comes out. The output gets a frame of its own, read off a real run —
compile it and paste; never type the output from memory. Where the run's
tie-breaks differ from the book's figure, say so and show it: it is the
cheapest possible lesson in what a tie is.

**When the code runs on a picture, the picture sits beside the code** and
advances as the voice walks the lines: one frame per round, the picture
showing that round's state, the line lit as it is named (`slides.md`, "Code
on slides"). A listing that does not fit beside the picture at readable size
is split across frames, never shrunk.

Style, the same in every chapter:

- 4-space indent, K&R braces (`{` on the same line), `for(`/`if(`/`while(`
  with no space before the paren, packed loop headers
  (`for(int i = 0; i < n; i++)`), spaces around `=` `==` `&&` `||`
- no optional braces: `if(!node) return;` on one line; single-statement
  bodies unbraced; a `for/for/if` cascade runs unbraced
- camelCase; `i j r c` for indices, `n m rows cols` for sizes; the answer is
  `result`; helpers named for what they do (`dfs`, `backtrack`)
- range-for and structured bindings (`for(auto [r, c] : cells)`); `auto`
  there and on a lambda, nowhere else; plain `int`; C++23 freely
  (`std::println`, `ranges::sort`, `contains`)
- state that several helpers share lives in members, `private:` first
- `//` comments above the line, lowercase, only where the invariant is not
  obvious — one *why*, never a label of what the line does
- whitespace between phases, not between every line
- lines short enough to sit beside a picture — about 55 characters

Compiling locally: GCC 13 ships no `<print>`; build with a shim
(`-include println_shim.h` defining `std::println` over `std::format`) so the
listing itself stays real C++23.
