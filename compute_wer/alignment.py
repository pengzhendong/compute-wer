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

from rapidfuzz.distance import Levenshtein


def get_opcodes(reference, hypothesis):
    """Yield per-token (op, ref_index, hyp_index) tuples."""
    for opcode in Levenshtein.opcodes(reference, hypothesis):
        op = opcode.tag
        if op == "equal" or op == "replace":
            for k in range(opcode.src_end - opcode.src_start):
                yield op, opcode.src_start + k, opcode.dest_start + k
        elif op == "delete":
            for k in range(opcode.src_end - opcode.src_start):
                yield op, opcode.src_start + k, opcode.dest_start
        elif op == "insert":
            for k in range(opcode.dest_end - opcode.dest_start):
                yield op, opcode.src_start, opcode.dest_start + k
