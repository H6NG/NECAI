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

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CXX) $(CXXFLAGS) -o $(TARGET) $(OBJS)

%.o: %.cpp
	$(CXX) $(CXXFLAGS) $(IFLAGS) -c $< -o $@

clean:
	rm -f $(OBJS) $(TARGET)
