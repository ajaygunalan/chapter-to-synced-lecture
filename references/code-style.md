# House style for staged code

Code the lecture writes (never the book's own, which stays as printed) is
C++, and looks the same in every chapter:

- 4-space indent, K&R braces (`{` on the same line), `for(`/`if(`/`while(`
  with no space before the paren, packed loop headers
  (`for(int i=0; i<n; i++)`), spaces around `=` `==` `&&` `||`
- no optional braces: `if(!node) return;` on one line; single-statement
  bodies unbraced; a `for/for/if` cascade runs unbraced
- camelCase; `i j r c` for indices, `n m rows cols` for sizes; the answer is
  `result`; helpers named for what they do (`dfs`, `backtrack`)
- range-for and structured bindings (`for(auto [r, c] : cells)`); `auto`
  there and nowhere else; plain `int`; C++20 freely (`ranges::sort`,
  `contains`)
- state that several helpers share lives in members, `private:` first
- `//` comments above the line, lowercase, only where the invariant is not
  obvious — one *why*, never a label of what the line does
- whitespace between phases, not between every line
