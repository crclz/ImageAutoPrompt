from typing import List, Tuple


class LlmParseService:

    @staticmethod
    def parse_exploration_output(s:str) -> Tuple[List[str], List[str]]:
        """
        extract from prompt0 to promptN-1
        """

        raise NotImplementedError()
