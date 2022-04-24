import pandas as pd
import datetime
from tkinter import *
from tkinter import filedialog
import os


def ageCalculator(birthDate, today):
    age = today.year - birthDate.year
    return age - 1 if (today.month, today.day) < (birthDate.month, birthDate.day) else age


def yearsDifferenceFormatter(start, end):
    return (end - start).days / 365.25


def Q1(age):
    if 18 <= age <= 29:
        return 0.07
    elif 30 <= age <= 39:
        return 0.05
    elif 40 <= age <= 49:
        return 0.04
    elif 50 <= age <= 59:
        return 0.03
    elif 60 <= age <= 67:
        return 0.02
    raise ValueError("Age must be between 18 to 67")


def Q2(age):
    if 18 <= age <= 29:
        return 0.2
    elif 30 <= age <= 39:
        return 0.13
    elif 40 <= age <= 49:
        return 0.1
    elif 50 <= age <= 59:
        return 0.07
    elif 60 <= age <= 67:
        return 0.03
    raise ValueError("Age must be between 18 to 67")


def Q3(age, gender):
    deathBoard = DEATH_BOARD_MEN if gender == 'M' else DEATH_BOARD_WOMEN
    row = (deathBoard['age'] == age)
    if row.sum() == 0:
        raise ValueError(f"Invalid age given: {age}")
    return float(deathBoard[row]['q(x)'])


def discountRate(year):
    row = DISCOUNT_RATE['שנה'] == year
    if row.sum() == 0:
        row = DISCOUNT_RATE['שנה'] == DISCOUNT_RATE['שנה'].max()
    return float(DISCOUNT_RATE[row]['שיעור היוון'])


def pX(age, t, gender):
    p = 1.0
    for i in range(age+1, age+t):
        p *= (1 - Q1(i) - Q2(i) - Q3(i, gender))
    return p


def compensationCalculator(w, age, lastSalary, seniority, sectionValue14, assetsValue, gender):
    return dismissalCompensation(w, age, lastSalary, seniority, sectionValue14, gender)+deathCompensation(w, age, lastSalary, seniority, sectionValue14, gender)+resignationCompensation(w, age, assetsValue, gender)+retirementCompensation(w, age, assetsValue, lastSalary, seniority, sectionValue14, gender)


def dismissalCompensation(w, age, lastSalary, seniority, sectionValue14, gender):
    compensation = 0
    growthSalary = 0.0
    for t in range(0, w-age-2):
        compensation += (lastSalary * seniority * (1-sectionValue14) * (((1+growthSalary) ** (
            t+0.5)) * pX(age, t+1, gender) * Q1(age+t+1) / (1 + discountRate(t+1)) ** (t+0.5)))
        growthSalary = 0.02
    return compensation


def deathCompensation(w, age, lastSalary, seniority, sectionValue14, gender):
    compensation = 0
    growthSalary = 0.0
    for t in range(0, w-age-2):
        compensation += (lastSalary * seniority * (1-sectionValue14) * (((1+growthSalary) ** (t+0.5))
                         * pX(age, t+1, gender) * Q3(age+t+1, gender) / (1 + discountRate(t+1)) ** (t+0.5)))
        growthSalary = 0.02
    return compensation


def resignationCompensation(w, age, assetsValue, gender):
    compensation = 0
    for t in range(0, w-age-2):
        compensation += assetsValue * pX(age, t+1, gender) * Q2(age+t+1)
    return compensation


def retirementCompensation(w, age, assetsValue, lastSalary, seniority, sectionValue14, gender):
    growthSalary = 0.02 if w-age-2 >= 1 else 0.0
    compensation = (lastSalary * seniority * (1-sectionValue14) * (((1+growthSalary) ** (w-age+1+0.5)
                    * pX(age, w-age-1, gender) * Q3(w-1, gender))/(1 + discountRate(w-1)) ** (w-age+1+0.5)))
    compensation += assetsValue * pX(age, w-age-1, gender) * Q2(w-1)
    compensation += (lastSalary * seniority * (1-sectionValue14) * (((1+growthSalary) ** (w-age) * pX(
        age, w-age-1, gender) * (1 - Q1(w-1) - Q2(w-1) - Q3(w-1, gender)))/(1 + discountRate(w-1)) ** (w-age)))
    return compensation


def compensationCalculatorTotal(employee):
    if pd.notna(employee["סיבת עזיבה"]):
        return 0

    employeeAge = ageCalculator(
        employee['תאריך לידה'], DATE_OF_CALCULATION)
    retirementAge = 67 if employee['מין'] == 'M' else 64

    employeeSeniority = yearsDifferenceFormatter(
        employee['תאריך תחילת עבודה'], DATE_OF_CALCULATION)

    employeeLastSalary = employee['שכר']

    if retirementAge <= employeeAge:
        return employeeLastSalary * employeeSeniority

    if employee['תאריך קבלת סעיף 14'] == employee['תאריך תחילת עבודה'] and (employee['אחוז סעיף 14'] == 100):
        return 0

    section14Available = (
        False if pd.isna(employee['אחוז סעיף 14']) else True)

    if section14Available:

        if employee['תאריך קבלת סעיף 14'] == employee['תאריך תחילת עבודה']:
            return compensationCalculator(retirementAge, employeeAge, employeeLastSalary, employeeSeniority, employee['אחוז סעיף 14'] / 100, employee['שווי נכס'], employee['מין'])

        else:
            if employee['אחוז סעיף 14'] == 100:
                noSection14Years = yearsDifferenceFormatter(
                    employee['תאריך תחילת עבודה'], employee['תאריך קבלת סעיף 14'])
                return compensationCalculator(retirementAge, employeeAge, employeeLastSalary, noSection14Years, 0, employee['שווי נכס'], employee['מין'])
            else:
                noSection14Years = yearsDifferenceFormatter(
                    employee['תאריך תחילת עבודה'], employee['תאריך קבלת סעיף 14'])
                years_with_section_14 = yearsDifferenceFormatter(
                    employee['תאריך קבלת סעיף 14'], DATE_OF_CALCULATION)
                return (compensationCalculator(retirementAge, employeeAge, employeeLastSalary, noSection14Years, 0, employee['שווי נכס'], employee['מין']) + compensationCalculator(retirementAge, employeeAge, employeeLastSalary, years_with_section_14, employee['אחוז סעיף 14'] / 100, employee['שווי נכס'], employee['מין']))
    return compensationCalculator(retirementAge, employeeAge, employeeLastSalary, employeeSeniority, 0, employee['שווי נכס'], employee['מין'])


if __name__ == '__main__':
    root = Tk()
    root.withdraw()
    DATE_OF_CALCULATION = datetime.datetime(2021, 12, 31)

    deathTablePath = filedialog.askopenfilename(
        initialdir="/", title="בחר לוח תמותה", filetypes=(("Excel files", "*.xlsx*"), ("all files", "*.*")))

    data2Path = filedialog.askopenfilename(
        initialdir="/", title="בחר קובץ מידע", filetypes=(("Excel files", "*.xlsx*"), ("all files", "*.*")))

    outputPath = filedialog.askdirectory(
        initialdir="/", title="בחר מיקום לקובץ פלט")

    DEATH_BOARD_MEN = pd.read_excel(
        deathTablePath, sheet_name="גברים", header=0, )

    DEATH_BOARD_WOMEN = pd.read_excel(
        deathTablePath, sheet_name="נשים", header=0)

    DISCOUNT_RATE = pd.read_excel(data2Path, sheet_name="הנחות", header=0)

    employment_data = pd.read_excel(
        data2Path, sheet_name="data", index_col=0, parse_dates=True)

    employment_data.loc[:, "תאריך לידה"] = (
        employment_data.loc[:, "תאריך לידה"].dt.normalize())
    employment_data.loc[:, "תאריך תחילת עבודה"] = (
        employment_data.loc[:, "תאריך תחילת עבודה"].dt.normalize())
    employment_data.loc[:, "תאריך קבלת סעיף 14"] = (
        employment_data.loc[:, "תאריך קבלת סעיף 14"].dt.normalize())
    employment_data.loc[:, "תאריך עזיבה"] = (pd.to_datetime(
        employment_data.loc[:, "תאריך עזיבה"], errors='coerce').dt.normalize())

    employment_data['פיצויים'] = employment_data.apply(
        compensationCalculatorTotal, axis=1)

    employment_data['פיצויים'].to_excel(
        os.path.join(outputPath, "output.xlsx"))
