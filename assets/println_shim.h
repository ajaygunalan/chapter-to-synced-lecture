// shim: GCC 13 has no <print>; std::print/println via std::format so the real source compiles unchanged
#include <format>
#include <cstdio>
#include <string>
namespace std {
  template <class... A> void print(format_string<A...> f, A&&... a) {
    fputs(vformat(f.get(), make_format_args(a...)).c_str(), stdout);
  }
  template <class... A> void println(format_string<A...> f, A&&... a) {
    fputs((vformat(f.get(), make_format_args(a...)) + "\n").c_str(), stdout);
  }
}
#define PRINT_SHIM 1
