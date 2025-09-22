TARGET = dfs_scheduler.exe
SRC = dfs_scheduler.c
CC = g++.exe
CFLAGS = -g -maes -mssse3
LDFLAGS = -lws2_32

all: $(TARGET)

$(TARGET): $(SRC)
	$(CC) $(CFLAGS) $(SRC) -o $(TARGET) $(LDFLAGS)

clean:
	del /Q $(TARGET)