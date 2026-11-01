.PHONY: install test step1 step2 step3 step5

install:
	@echo "Для практик 1–2 ничего устанавливать не нужно."

test: step1 step2 step3 step5

step1:
	@$(MAKE) -s -C practices/practice_01 test

step2:
	@$(MAKE) -s -C practices/practice_02 test

step3:
	@$(MAKE) -s -C practices/practice_03 test

step5:
	@$(MAKE) -s -C practices/practice_05 test
