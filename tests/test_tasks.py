from copy import deepcopy
from unittest.case import TestCase

from datasets.arrow_dataset import Dataset
from datasets.features import ClassLabel, Features, Sequence, Value
from datasets.info import DatasetInfo
from datasets.tasks import (
    AutomaticSpeechRecognition,
    ImageClassification,
    QuestionAnsweringExtractive,
    Summarization,
    TextClassification,
)


SAMPLE_QUESTION_ANSWERING_EXTRACTIVE = {
    "id": "5733be284776f41900661182",
    "title": "University_of_Notre_Dame",
    "context": 'Architecturally, the school has a Catholic character. Atop the Main Building\'s gold dome is a golden statue of the Virgin Mary. Immediately in front of the Main Building and facing it, is a copper statue of Christ with arms upraised with the legend "Venite Ad Me Omnes". Next to the Main Building is the Basilica of the Sacred Heart. Immediately behind the basilica is the Grotto, a Marian place of prayer and reflection. It is a replica of the grotto at Lourdes, France where the Virgin Mary reputedly appeared to Saint Bernadette Soubirous in 1858. At the end of the main drive (and in a direct line that connects through 3 statues and the Gold Dome), is a simple, modern stone statue of Mary.',
    "question": "To whom did the Virgin Mary allegedly appear in 1858 in Lourdes France?",
    "answers": {"text": ["Saint Bernadette Soubirous"], "answer_start": [515]},
}


class TextClassificationTest(TestCase):
    def setUp(self):
        self.labels = sorted(["pos", "neg"])

    def test_column_mapping(self):
        task = TextClassification(text_column="input_text", label_column="input_label", labels=self.labels)
        self.assertDictEqual({"input_text": "text", "input_label": "labels"}, task.column_mapping)

    def test_from_dict(self):
        input_schema = Features({"text": Value("string")})
        # Labels are cast to tuple during `TextClassification.__post_init__`, so we do the same here
        label_schema = Features({"labels": ClassLabel(names=tuple(self.labels))})
        template_dict = {"text_column": "input_text", "label_column": "input_labels", "labels": self.labels}
        task = TextClassification.from_dict(template_dict)
        self.assertEqual("text-classification", task.task)
        self.assertEqual(input_schema, task.input_schema)
        self.assertEqual(label_schema, task.label_schema)

    def test_value_error_unique_labels(self):
        with self.assertRaises(ValueError):
            # Add duplicate labels
            labels = self.labels + self.labels[:1]
            task = TextClassification(text_column="input_text", label_column="input_label", labels=labels)
            self.assertEqual("text-classification", task.task)


class QuestionAnsweringTest(TestCase):
    def test_column_mapping(self):
        task = QuestionAnsweringExtractive(
            context_column="input_context", question_column="input_question", answers_column="input_answers"
        )
        self.assertDictEqual(
            {"input_context": "context", "input_question": "question", "input_answers": "answers"}, task.column_mapping
        )

    def test_from_dict(self):
        input_schema = Features({"question": Value("string"), "context": Value("string")})
        label_schema = Features(
            {
                "answers": Sequence(
                    {
                        "text": Value("string"),
                        "answer_start": Value("int32"),
                    }
                )
            }
        )
        template_dict = {
            "context_column": "input_input_context",
            "question_column": "input_question",
            "answers_column": "input_answers",
        }
        task = QuestionAnsweringExtractive.from_dict(template_dict)
        self.assertEqual("question-answering-extractive", task.task)
        self.assertEqual(input_schema, task.input_schema)
        self.assertEqual(label_schema, task.label_schema)


class SummarizationTest(TestCase):
    def test_column_mapping(self):
        task = Summarization(text_column="input_text", summary_column="input_summary")
        self.assertDictEqual({"input_text": "text", "input_summary": "summary"}, task.column_mapping)

    def test_from_dict(self):
        input_schema = Features({"text": Value("string")})
        label_schema = Features({"summary": Value("string")})
        template_dict = {"text_column": "input_text", "summary_column": "input_summary"}
        task = Summarization.from_dict(template_dict)
        self.assertEqual("summarization", task.task)
        self.assertEqual(input_schema, task.input_schema)
        self.assertEqual(label_schema, task.label_schema)


class AutomaticSpeechRecognitionTest(TestCase):
    def test_column_mapping(self):
        task = AutomaticSpeechRecognition(
            audio_file_path_column="input_audio_file_path", transcription_column="input_transcription"
        )
        self.assertDictEqual(
            {"input_audio_file_path": "audio_file_path", "input_transcription": "transcription"}, task.column_mapping
        )

    def test_from_dict(self):
        input_schema = Features({"audio_file_path": Value("string")})
        label_schema = Features({"transcription": Value("string")})
        template_dict = {
            "audio_file_path_column": "input_audio_file_path",
            "transcription_column": "input_transcription",
        }
        task = AutomaticSpeechRecognition.from_dict(template_dict)
        self.assertEqual("automatic-speech-recognition", task.task)
        self.assertEqual(input_schema, task.input_schema)
        self.assertEqual(label_schema, task.label_schema)


class ImageClassificationTest(TestCase):
    def setUp(self):
        self.labels = sorted(["pos", "neg"])

    def test_column_mapping(self):
        task = ImageClassification(image_file_path_column="file_paths", label_column="input_label")
        self.assertDictEqual({"file_paths": "image_file_path", "input_label": "labels"}, task.column_mapping)

    def test_from_dict(self):
        input_schema = Features({"image_file_path": Value("string")})
        label_schema = Features({"labels": ClassLabel(names=tuple(self.labels))})
        template_dict = {
            "image_file_path_column": "input_image_file_path",
            "label_column": "input_label",
            "labels": self.labels,
        }
        task = ImageClassification.from_dict(template_dict)
        self.assertEqual("image-classification", task.task)
        self.assertEqual(input_schema, task.input_schema)
        self.assertEqual(label_schema, task.label_schema)


class DatasetWithTaskProcessingTest(TestCase):
    def test_map_on_task_template(self):
        info = DatasetInfo(task_templates=QuestionAnsweringExtractive())
        dataset = Dataset.from_dict({k: [v] for k, v in SAMPLE_QUESTION_ANSWERING_EXTRACTIVE.items()}, info=info)
        assert isinstance(dataset.info.task_templates, list)
        assert len(dataset.info.task_templates) == 1

        def keep_task(x):
            return x

        def dont_keep_task(x):
            out = deepcopy(SAMPLE_QUESTION_ANSWERING_EXTRACTIVE)
            out["answers"]["foobar"] = 0
            return out

        mapped_dataset = dataset.map(keep_task)
        assert mapped_dataset.info.task_templates == dataset.info.task_templates
        # reload from cache
        mapped_dataset = dataset.map(keep_task)
        assert mapped_dataset.info.task_templates == dataset.info.task_templates

        mapped_dataset = dataset.map(dont_keep_task)
        assert mapped_dataset.info.task_templates == []
        # reload from cache
        mapped_dataset = dataset.map(dont_keep_task)
        assert mapped_dataset.info.task_templates == []

    def test_remove_and_map_on_task_template(self):
        features = Features({"text": Value("string"), "label": ClassLabel(names=("pos", "neg"))})
        task_templates = TextClassification(text_column="text", label_column="label")
        info = DatasetInfo(features=features, task_templates=task_templates)
        dataset = Dataset.from_dict({"text": ["A sentence."], "label": ["pos"]}, info=info)

        def process(example):
            return example

        modified_dataset = dataset.remove_columns("label")
        mapped_dataset = modified_dataset.map(process)
        assert mapped_dataset.info.task_templates == []
