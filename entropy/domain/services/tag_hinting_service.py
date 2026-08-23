from typing import List

from entropy.domain.services.tag_checker import TagChecker


class TagHintingService:
    @classmethod
    def get_invalid_tag_hint(cls, positives: List[str], negatives: List[str], tolerance: int) -> str:
        """
        if invalid tag count not exceed tolerance, return empty
        Otherwise return hint text.
        """

        assert len(positives) == len(negatives)

        not_exist_tags_list: List[List[str]] = []

        for positive, negative in zip(positives, negatives):
            not_exist_positive = TagChecker.get_not_exist_tags(positive)
            not_exist_negative = TagChecker.get_not_exist_tags(negative)

            not_exist_tags = not_exist_positive + not_exist_negative
            not_exist_tags = list(set(not_exist_tags))

            not_exist_tags_list.append(not_exist_tags)

        max_invalid_tag_count = max([len(p) for p in not_exist_tags_list])
        if max_invalid_tag_count <= tolerance:
            return ""

        lines = []

        lines.append(
            "system: 非标准的 danbooru tag 不必清零：预算内保留少量非标准 tag 可以提升表现力，"
            "但超过预算会干扰出图稳定性。请把无效 tag 数量控制在预算内，"
            "并将预算分配给最值得保留的 tag（优先保留表达关键特征的 tag，替换掉可有可无的）。"
        )

        for i, not_exist_tags in enumerate(not_exist_tags_list):
            if len(not_exist_tags) <= tolerance:
                continue

            lines.append(
                f"system: prompt[{i}] found {len(not_exist_tags)} invalid tags, which exceeds budget={tolerance}"
            )

            for invalid_tag in not_exist_tags:
                lines.append(f"invalid tag: {invalid_tag}")

        lines.append("")

        return "\n".join(lines)
