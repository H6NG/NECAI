CXX = g++
CXXFLAGS = -std=c++17 -O2 -Wall -Wextra

TARGET = necai_engine

SRCS = main.cpp board.cpp moves.cpp search.cpp eval.cpp move.cpp
OBJS = $(SRCS:.cpp=.o)

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CXX) $(CXXFLAGS) -o $(TARGET) $(OBJS)

%.o: %.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

clean:
	rm -f $(OBJS) $(TARGET)