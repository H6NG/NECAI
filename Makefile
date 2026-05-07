CXX = g++
CXXFLAGS = -std=c++17 -O2 -Wall -Wextra
IFLAGS = -I documentation -I engine -I evaluator/classical_eval

TARGET = necai_engine

SRCS = main.cpp \
       documentation/board.cpp \
       documentation/moves.cpp \
       documentation/move.cpp \
       evaluator/classical_eval/eval.cpp \
       engine/search.cpp

OBJS = $(SRCS:.cpp=.o)

EVAL_STREAM = eval_stream
EVAL_STREAM_SRCS = evaluator/classical_eval/eval_stream.cpp \
                   documentation/board.cpp \
                   documentation/moves.cpp \
                   documentation/move.cpp \
                   evaluator/classical_eval/eval.cpp
EVAL_STREAM_OBJS = $(EVAL_STREAM_SRCS:.cpp=.o)

TOP_MOVES = top_moves
TOP_MOVES_SRCS = engine/top_moves.cpp \
                 documentation/board.cpp \
                 documentation/moves.cpp \
                 documentation/move.cpp \
                 evaluator/classical_eval/eval.cpp \
                 engine/search.cpp
TOP_MOVES_OBJS = $(TOP_MOVES_SRCS:.cpp=.o)

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CXX) $(CXXFLAGS) -o $(TARGET) $(OBJS)

$(EVAL_STREAM): $(EVAL_STREAM_OBJS)
	$(CXX) $(CXXFLAGS) -o $(EVAL_STREAM) $(EVAL_STREAM_OBJS)

$(TOP_MOVES): $(TOP_MOVES_OBJS)
	$(CXX) $(CXXFLAGS) -o $(TOP_MOVES) $(TOP_MOVES_OBJS)

%.o: %.cpp
	$(CXX) $(CXXFLAGS) $(IFLAGS) -c $< -o $@

clean:
	rm -f $(OBJS) $(EVAL_STREAM_OBJS) $(TOP_MOVES_OBJS) $(TARGET) $(EVAL_STREAM) $(TOP_MOVES)
