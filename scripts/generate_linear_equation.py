# scripts/generate_linear_equation.py
from scripts.answer_sheet.generator import StudentAnswerSheetGenerator


def main():
    generator = StudentAnswerSheetGenerator()

    question_no = 1
    score = 5
    # question_text = "小明去文具店买铅笔和笔记本。\n铅笔每支 3 元，笔记本 5 元。\n小明一共花了 23 元，买了一本笔记本。\n请问小明买了几支铅笔？"
    student_steps = [
        "设购买铅笔 x 支",
        "FORMULA:3x + 5 = 23",
        "FORMULA:3x = 23 - 5",
        "FORMULA:3x = 18",
        "FORMULA:x = 6"
    ]
    answer_text = "小明买了 6 支铅笔"

    generator.generate_answer_sheet(
        question_no=question_no,
        score=score,
        student_steps=student_steps,
        answer_text=answer_text,
        filename="linear_equation_answer.png"
    )


if __name__ == "__main__":
    main()
