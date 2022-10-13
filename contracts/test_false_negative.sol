


contract example {
	// Process state
	function get_pid_state(uint64 _pid)  public returns (uint64) {
		uint64 n = 8;
		for (uint16 i = 1; i < 4; ++i) {
			if ((i % 3) == 0) {
				n *= _pid / uint64(i);
			} else {
				n /= 3;
			}
		}
		return n % uint64(5);
	}

}