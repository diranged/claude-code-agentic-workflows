ACTION_DIRS := $(sort $(dir $(wildcard */Makefile)))

.PHONY: test
test:
	@for dir in $(ACTION_DIRS); do \
		echo "=== Testing $$dir ==="; \
		$(MAKE) -C $$dir test || exit 1; \
	done
