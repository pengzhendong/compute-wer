# Copyright (c) 2025, Zhendong Peng (pzd17@tsinghua.org.cn)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from edit_distance import SequenceMatcher


class Calculator:

    def __init__(self):
        self.data = {}
        self.op_map = {"equal": "cor", "replace": "sub", "insert": "ins", "delete": "del"}

    def calculate(self, lab, rec):
        for token in lab + rec:
            self.data.setdefault(token, {op: 0 for op in ["all", "cor", "sub", "ins", "del"]})

        result = {"lab": [], "rec": [], "all": 0, "cor": 0, "sub": 0, "ins": 0, "del": 0}
        i, j = 0, 0
        for op, *_ in SequenceMatcher(lab, rec).get_opcodes():
            op = self.op_map[op]
            result[op] += 1
            result["lab"].append(lab[i] if op != "ins" else "")
            result["rec"].append(rec[j] if op != "del" else "")
            self.data[lab[i] if op != "ins" else rec[j]][op] += 1
            if op != "ins":
                result["all"] += 1
                self.data[lab[i]]["all"] += 1
                i += 1
            j += op != "del"
        return result

    def overall(self):
        result = {op: 0 for op in ["all", "cor", "sub", "ins", "del"]}
        for token in self.data.values():
            for op in result:
                result[op] += token[op]
        return result

    def cluster(self, data):
        result = {op: 0 for op in ["all", "cor", "sub", "ins", "del"]}
        for token in data:
            if token not in self.data:
                continue
            for op, count in self.data[token].items():
                result[op] += count
        return result
