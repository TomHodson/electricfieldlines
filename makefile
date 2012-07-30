CC=gcc
CFLAGS=-Wall --std=gnu99 -lm


drawlines.so : drawlines.c
	$(CC) -shared -fPIC $(CFLAGS) -Wl,-soname,$@ -o $@ $<

.PHONY: clean
clean:
	rm -rf *.o *.so *.pyc *~ *.bak
