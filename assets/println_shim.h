// shim: GCC 13 has no <print>; std::println via std::format so the real source compiles unchanged
#include <format>
#include <cstdio>
#include <string_view>
namespace std {
  template <class... A> void println(format_string<A...> f, A&&... a) {
    fputs((vformat(f.get(), make_format_args(a...)) + "\n").c_str(), stdout);
  }
}
#define PRINT_SHIM 1
