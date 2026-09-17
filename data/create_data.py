import os
import pandas as pd
from fpdf import FPDF
from pathlib import Path

def create_pdf(year, rev, exp, gp, op, np, ta, tl, eq, ca, cl, cash, path):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Page 1
    pdf.add_page()
    pdf.set_font('helvetica', 'B', 18)
    pdf.cell(0, 12, 'NovaTech Holdings - Annual Financial Report ' + str(year), new_x='LMARGIN', new_y='NEXT', align='C')
    pdf.set_font('helvetica', 'I', 11)
    pdf.cell(0, 8, 'Fiscal Year Ended December 31, ' + str(year) + ' | Currency: USD (United States Dollars)', new_x='LMARGIN', new_y='NEXT', align='C')
    pdf.ln(6)
    
    pdf.set_font('helvetica', 'B', 13)
    pdf.cell(0, 8, '1. Company Overview', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('helvetica', '', 10)
    pdf.multi_cell(0, 6, 'NovaTech Holdings is a global enterprise software and financial analytics provider. In ' + str(year) + ', the company demonstrated remarkable financial stability, expanded its recurring cloud SaaS subscription footprint, and delivered record client satisfaction across international markets.')
    pdf.ln(4)
    
    pdf.set_font('helvetica', 'B', 13)
    pdf.cell(0, 8, '2. Financial Performance & Income Statement', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('helvetica', '', 10)
    rev_m = rev // 1000000
    perf = (
        'For the fiscal year ' + str(year) + ', NovaTech achieved total Revenue of USD ' + f'{rev:,}' +
        ' (' + str(rev_m) + ' million USD), reflecting strong market demand. ' +
        'Total Operating Expenses were USD ' + f'{exp:,}' + '. ' +
        'Gross Profit reached USD ' + f'{gp:,}' + '. ' +
        'Operating Profit (EBIT) was recorded at USD ' + f'{op:,}' + ', and ' +
        'Net Profit (Net Income) was USD ' + f'{np:,}' + ' (' + str(np // 1000000) + ' million USD).'
    )
    pdf.multi_cell(0, 6, perf)
    pdf.ln(4)

    pdf.set_font('helvetica', 'B', 13)
    pdf.cell(0, 8, '3. Balance Sheet Summary', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('helvetica', '', 10)
    ta_m = ta // 1000000
    bs = (
        'As of December 31, ' + str(year) + ', Total Assets were USD ' + f'{ta:,}' + ' (' + str(ta_m) + ' million USD). ' +
        'Current Assets stood at USD ' + f'{ca:,}' + ', including Cash and Cash Equivalents of USD ' + f'{cash:,}' + '. ' +
        'Total Liabilities were USD ' + f'{tl:,}' + ', of which Current Liabilities were USD ' + f'{cl:,}' + '. ' +
        'Total Shareholders Equity concluded the year at USD ' + f'{eq:,}' + '.'
    )
    pdf.multi_cell(0, 6, bs)
    pdf.ln(4)

    # Page 2
    pdf.add_page()
    pdf.set_font('helvetica', 'B', 13)
    pdf.cell(0, 8, '4. Cash Flow Statement Summary', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('helvetica', '', 10)
    cf = (
        'Operating Cash Flow for fiscal year ' + str(year) + ' was robust at USD ' + f'{(np + 12000000):,}' + '. ' +
        'Capital expenditures totaled USD 18,000,000 targeted at enterprise AI modernization and secure infrastructure. ' +
        'Cash and Cash Equivalents at year end reached USD ' + f'{cash:,}' + '.'
    )
    pdf.multi_cell(0, 6, cf)
    pdf.ln(4)

    pdf.set_font('helvetica', 'B', 13)
    pdf.cell(0, 8, '5. Financial Highlights & Milestones', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('helvetica', '', 10)
    hl = (
        '- Total Revenue achieved: USD ' + f'{rev:,}' + ' in ' + str(year) + '.\n' +
        '- Net Profit achieved: USD ' + f'{np:,}' + ' with disciplined operating margins.\n' +
        '- Cash and Cash Equivalents reserve: USD ' + f'{cash:,}' + '.\n' +
        '- Conservative debt-to-equity posture and strong balance sheet health.'
    )
    pdf.multi_cell(0, 6, hl)
    pdf.ln(4)

    pdf.set_font('helvetica', 'B', 13)
    pdf.cell(0, 8, '6. Financial Risks and Market Concerns', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('helvetica', '', 10)
    risks = (
        'Key financial and operational risks identified in ' + str(year) + ' include foreign currency exposure, ' +
        'global interest rate fluctuations, cybersecurity compliance requirements, and rising cloud server hosting costs.'
    )
    pdf.multi_cell(0, 6, risks)

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    pdf.output(path)
    print('Generated: ' + path)

def create_terms(path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('helvetica', 'B', 16)
    pdf.cell(0, 10, 'Financial Terminology and KPI Reference Guide', new_x='LMARGIN', new_y='NEXT', align='C')
    pdf.ln(8)
    
    terms = [
        ('Revenue', 'Total gross sales and receipts generated from primary business operations.'),
        ('Net Profit (Net Income)', 'Net earnings remaining after deducting all expenses, depreciation, interest, and taxes.'),
        ('Gross Profit', 'Revenue minus Cost of Goods Sold (COGS). Indicates core production efficiency.'),
        ('Operating Profit (EBIT)', 'Earnings before interest and taxes generated strictly from ongoing operations.'),
        ('Total Assets', 'Aggregate value of all current and long-term economic resources owned by the entity.'),
        ('Total Liabilities', 'Total financial obligations and claims held by creditors against the entity.'),
        ('Shareholders Equity', 'Net book value of the enterprise calculated as Total Assets minus Total Liabilities.'),
        ('Current Assets & Current Liabilities', 'Short-term economic resources realizable within one year versus short-term debts due within one year.'),
        ('Cash and Cash Equivalents', 'Bank deposits, commercial paper, and short-term liquid treasury investments.')
    ]
    
    for term, definition in terms:
        pdf.set_font('helvetica', 'B', 11)
        pdf.cell(0, 7, term, new_x='LMARGIN', new_y='NEXT')
        pdf.set_font('helvetica', '', 10)
        pdf.multi_cell(0, 5, definition)
        pdf.ln(3)
        
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    pdf.output(path)
    print('Generated: ' + path)

def create_csv(path):
    data = [
        {
            'Year': 2023,
            'Company': 'NovaTech Holdings',
            'Revenue': 125000000,
            'Expenses': 80000000,
            'Gross_Profit': 45000000,
            'Operating_Profit': 25000000,
            'Net_Profit': 15000000,
            'Total_Assets': 600000000,
            'Total_Liabilities': 280000000,
            'Shareholders_Equity': 320000000,
            'Current_Assets': 210000000,
            'Current_Liabilities': 95000000,
            'Cash_and_Equivalents': 65000000,
            'Currency': 'USD'
        },
        {
            'Year': 2024,
            'Company': 'NovaTech Holdings',
            'Revenue': 150000000,
            'Expenses': 95000000,
            'Gross_Profit': 55000000,
            'Operating_Profit': 32000000,
            'Net_Profit': 20000000,
            'Total_Assets': 720000000,
            'Total_Liabilities': 310000000,
            'Shareholders_Equity': 410000000,
            'Current_Assets': 260000000,
            'Current_Liabilities': 110000000,
            'Cash_and_Equivalents': 85000000,
            'Currency': 'USD'
        }
    ]
    df = pd.DataFrame(data)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    print('Generated: ' + path)

create_pdf(2023, 125000000, 80000000, 45000000, 25000000, 15000000, 600000000, 280000000, 320000000, 210000000, 95000000, 65000000, 'data/sample_reports/annual_report_2023.pdf')
create_pdf(2024, 150000000, 95000000, 55000000, 32000000, 20000000, 720000000, 310000000, 410000000, 260000000, 110000000, 85000000, 'data/sample_reports/annual_report_2024.pdf')
create_terms('data/sample_reports/financial_terminology.pdf')
create_csv('data/financial_csv/financial_kpi_dataset.csv')
create_csv('data/balance_sheet.csv')
create_pdf(2024, 150000000, 95000000, 55000000, 32000000, 20000000, 720000000, 310000000, 410000000, 260000000, 110000000, 85000000, 'data/annual_report.pdf')
