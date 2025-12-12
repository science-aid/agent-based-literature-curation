import json

import numpy as np

from biomni.task.base_task import base_task


class CustomBenchmark(base_task):
    def __init__(self, jsonl_path="./data/test_evaldata.jsonl"):
        # JSONLファイルを読み込み
        data = []
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                data.append(json.loads(line.strip()))

        # Lab-Benchと同じプロンプト形式を使用
        self.prompt = """The following is a multiple choice question about biology.  
Please answer by responding with the letter of the correct answer.  
  
Question: {question}  
Options:  
{options}  
  
You MUST include the letter of the correct answer within the following tags:  
[ANSWER] and [/ANSWER]. For example, '[ANSWER]<answer>[/ANSWER]',  
where <answer> is the correct letter. Always answer in exactly this format  
of a single letter between the two tags, even if you are unsure.  
We require this because we use automatic parsing.  
        """

        # データを処理してLab-Benchと同じ形式に変換
        np.random.seed(42)
        processed_data = []

        for item in data:
            # 選択肢を作成（ideal + distractors）
            options = [item["ideal"]] + item["distractors"]
            np.random.shuffle(options)

            # 選択肢に文字ラベル（A, B, C, D）を付与
            options_letters = "\n".join(
                [chr(ord("A") + i) + "." + opt for i, opt in enumerate(options)]
            )

            # 正解の文字ラベルを計算
            correct_index = options.index(item["ideal"])
            letter_answer = chr(ord("A") + correct_index)

            processed_data.append(
                {
                    "id": item["id"],
                    "question": item["question"],
                    "options": options,
                    "options_letters": options_letters,
                    "letter_answer": letter_answer,
                    "ideal": item["ideal"],
                }
            )

        # データを配列として保存
        self.query = [item["question"] for item in processed_data]
        self.options = [item["options_letters"] for item in processed_data]
        self.answer = [item["letter_answer"] for item in processed_data]
        self.ids = [item["id"] for item in processed_data]

    def __len__(self):
        return len(self.query)

    def get_example(self, index=None):
        if index is None:
            index = np.random.randint(len(self.query))

        return {
            "prompt": self.prompt.format(
                question=self.query[index], options=self.options[index]
            ),
            "answer": self.answer[index],
        }

    def get_iterator(self):
        for i in range(len(self.query)):
            yield self.get_example(i)

    def evaluate(self, responses):
        from sklearn.metrics import accuracy_score

        ground_truth = self.answer
        responses = np.array(responses)

        return {
            "accuracy": accuracy_score(ground_truth, responses),
        }

    def output_class(self):
        from pydantic import BaseModel, Field

        class MultipleChoiceOutput(BaseModel):
            choice: str = Field(description="Multiple choice answer (A, B, C, or D)")

        return MultipleChoiceOutput
