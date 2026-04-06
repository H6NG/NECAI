#include <chrono>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <random>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

struct MemoEntry {
    std::string color;
    std::string current_move;
    std::string next_move;
};

struct LoadStats {
    std::size_t loaded = 0;
    std::size_t duplicates = 0;
};

struct BenchmarkStats {
    std::size_t lookups = 0;
    std::size_t found = 0;
    double total_ns = 0.0;
    double avg_ns = 0.0;
    double avg_us = 0.0;
};

using MemoTable = std::unordered_map<std::string, MemoEntry>;

namespace {

std::string extract_json_string(const std::string& line, const std::string& key) {
    const std::string pattern = "\"" + key + "\":\"";
    std::size_t pos = line.find(pattern);
    if (pos == std::string::npos) {
        return "";
    }

    pos += pattern.size();
    std::string value;
    bool escape = false;

    for (; pos < line.size(); ++pos) {
        char ch = line[pos];

        if (escape) {
            switch (ch) {
                case '\\': value.push_back('\\'); break;
                case '"': value.push_back('"'); break;
                case '/': value.push_back('/'); break;
                case 'n': value.push_back('\n'); break;
                case 'r': value.push_back('\r'); break;
                case 't': value.push_back('\t'); break;
                default: value.push_back(ch); break;
            }
            escape = false;
            continue;
        }

        if (ch == '\\') {
            escape = true;
            continue;
        }

        if (ch == '"') {
            break;
        }

        value.push_back(ch);
    }

    return value;
}

bool starts_with(const std::string& arg, const std::string& prefix) {
    return arg.rfind(prefix, 0) == 0;
}

void print_usage(const char* prog) {
    std::cout
        << "Usage: " << prog << " [options]\n"
        << "Options:\n"
        << "  --white=PATH         White memoization JSONL path\n"
        << "  --black=PATH         Black memoization JSONL path\n"
        << "  --limit=N            Max unique FEN rows to load (0 = all)\n"
        << "  --lookups=N          Number of hit and miss lookups to benchmark\n"
        << "  --seed=N             Random seed for probe generation\n"
        << "  --help               Show this help message\n";
}

LoadStats load_jsonl(
    const std::filesystem::path& path,
    MemoTable& table,
    std::vector<std::string>& keys,
    std::size_t limit
) {
    std::ifstream input(path);
    if (!input) {
        throw std::runtime_error("Could not open " + path.string());
    }

    LoadStats stats;
    std::string line;

    while (std::getline(input, line)) {
        if (limit != 0 && stats.loaded >= limit) {
            break;
        }

        const std::string fen = extract_json_string(line, "fen");
        if (fen.empty()) {
            continue;
        }

        MemoEntry entry {
            extract_json_string(line, "color"),
            extract_json_string(line, "current_move"),
            extract_json_string(line, "next_move"),
        };

        auto [it, inserted] = table.emplace(fen, std::move(entry));
        if (!inserted) {
            ++stats.duplicates;
            it->second = MemoEntry {
                extract_json_string(line, "color"),
                extract_json_string(line, "current_move"),
                extract_json_string(line, "next_move"),
            };
            continue;
        }

        keys.push_back(fen);
        ++stats.loaded;
    }

    return stats;
}

std::vector<std::string> build_hit_probes(
    const std::vector<std::string>& keys,
    std::size_t lookups,
    std::mt19937_64& rng
) {
    if (keys.empty()) {
        throw std::runtime_error("No memoization keys were loaded");
    }

    std::uniform_int_distribution<std::size_t> dist(0, keys.size() - 1);
    std::vector<std::string> probes;
    probes.reserve(lookups);

    for (std::size_t i = 0; i < lookups; ++i) {
        probes.push_back(keys[dist(rng)]);
    }

    return probes;
}

std::vector<std::string> build_miss_probes(const std::vector<std::string>& hit_probes) {
    std::vector<std::string> probes;
    probes.reserve(hit_probes.size());

    for (const auto& key : hit_probes) {
        probes.push_back(key + " |miss");
    }

    return probes;
}

BenchmarkStats benchmark_lookup(const MemoTable& table, const std::vector<std::string>& probes) {
    volatile std::size_t sink = 0;
    std::size_t found = 0;

    const auto start = std::chrono::steady_clock::now();
    for (const auto& probe : probes) {
        auto it = table.find(probe);
        if (it != table.end()) {
            ++found;
            sink += it->second.current_move.size();
            sink += it->second.next_move.size();
        } else {
            sink += probe.size() & 1U;
        }
    }
    const auto end = std::chrono::steady_clock::now();

    const auto total_ns_int =
        std::chrono::duration_cast<std::chrono::nanoseconds>(end - start).count();
    const double total_ns = static_cast<double>(total_ns_int);
    const double avg_ns = probes.empty() ? 0.0 : total_ns / static_cast<double>(probes.size());

    if (sink == std::numeric_limits<std::size_t>::max()) {
        std::cerr << "Impossible sink value\n";
    }

    return BenchmarkStats {
        probes.size(),
        found,
        total_ns,
        avg_ns,
        avg_ns / 1000.0,
    };
}

void print_stats(const std::string& label, const BenchmarkStats& stats) {
    std::cout << label << ":\n";
    std::cout << "  lookups: " << stats.lookups << "\n";
    std::cout << "  found: " << stats.found << "\n";
    std::cout << "  total_ns: " << std::fixed << std::setprecision(0) << stats.total_ns << "\n";
    std::cout << "  avg_ns: " << std::fixed << std::setprecision(2) << stats.avg_ns << "\n";
    std::cout << "  avg_us: " << std::fixed << std::setprecision(4) << stats.avg_us << "\n";
}

}  // namespace

int main(int argc, char* argv[]) {
    std::filesystem::path white_path = "../../necai/memoization/white/train.jsonl";
    std::filesystem::path black_path = "../../necai/memoization/black/train.jsonl";
    std::size_t limit = 0;
    std::size_t lookups = 1000000;
    std::uint64_t seed = 42;

    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "--help") {
            print_usage(argv[0]);
            return 0;
        }
        if (starts_with(arg, "--white=")) {
            white_path = arg.substr(8);
            continue;
        }
        if (starts_with(arg, "--black=")) {
            black_path = arg.substr(8);
            continue;
        }
        if (starts_with(arg, "--limit=")) {
            limit = static_cast<std::size_t>(std::stoull(arg.substr(8)));
            continue;
        }
        if (starts_with(arg, "--lookups=")) {
            lookups = static_cast<std::size_t>(std::stoull(arg.substr(10)));
            continue;
        }
        if (starts_with(arg, "--seed=")) {
            seed = static_cast<std::uint64_t>(std::stoull(arg.substr(7)));
            continue;
        }

        std::cerr << "Unknown argument: " << arg << "\n";
        print_usage(argv[0]);
        return 1;
    }

    MemoTable table;
    std::vector<std::string> keys;
    table.reserve(250000);
    keys.reserve(250000);

    const LoadStats white_stats = load_jsonl(white_path, table, keys, limit);
    LoadStats black_stats;
    if (limit == 0) {
        black_stats = load_jsonl(black_path, table, keys, 0);
    } else if (white_stats.loaded < limit) {
        black_stats = load_jsonl(black_path, table, keys, limit - white_stats.loaded);
    }

    std::mt19937_64 rng(seed);
    const auto hit_probes = build_hit_probes(keys, lookups, rng);
    const auto miss_probes = build_miss_probes(hit_probes);

    const BenchmarkStats hit_stats = benchmark_lookup(table, hit_probes);
    const BenchmarkStats miss_stats = benchmark_lookup(table, miss_probes);

    std::cout << "Memoization benchmark\n";
    std::cout << "  unique_entries: " << table.size() << "\n";
    std::cout << "  white_loaded: " << white_stats.loaded << "\n";
    std::cout << "  black_loaded: " << black_stats.loaded << "\n";
    std::cout << "  duplicates_overwritten: "
              << (white_stats.duplicates + black_stats.duplicates) << "\n";
    std::cout << "  data_structure: std::unordered_map<std::string, MemoEntry>\n";
    std::cout << "  average_case_lookup: O(1)\n";
    std::cout << "  sub_microsecond_hit_target_met: "
              << (hit_stats.avg_ns < 1000.0 ? "yes" : "no") << "\n";

    print_stats("Hit benchmark", hit_stats);
    print_stats("Miss benchmark", miss_stats);

    return 0;
}
