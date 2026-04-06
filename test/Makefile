CXX = g++
CXXFLAGS = -std=c++17 -O2 -Wall -Wextra -I../engine/cpp

TARGET = lmc
SRCS = lmc.cpp ../engine/cpp/board.cpp ../engine/cpp/moves.cpp ../engine/cpp/move.cpp

all: $(TARGET)

$(TARGET): $(SRCS)
	$(CXX) $(CXXFLAGS) -o $(TARGET) $(SRCS)

clean:
	rm -f $(TARGET)
