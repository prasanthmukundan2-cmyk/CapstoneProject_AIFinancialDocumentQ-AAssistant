import os
import pandas as pd
from fpdf import FPDF
from pathlib import Path

def create_pdf_report(year, revenue, expenses, gross_profit, operating_profit, net_profit, 
                      total_assets, total_liabilities, equity, current_assets, current_liabilities, 
                      cash, filename):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Page 1: Overview & Performance
    pdf.add_page()
    pdf.set_font('helvetica', 'B', 18)
    pdf.cell(0, 12, f'NovaTech Holdings - Annual Financial Report {year}', new_x='LMARGIN', new_y='NEXT', align='C')
    pdf.set_font('helvetica', 'I', 11)
    pdf.cell(0, 8, f'Fiscal Year Ended December 31, {year} | Currency: USD ($)', new_x='LMARGIN', new_y='NEXT', align='C')
    pdf.ln(6)
    
    pdf.set_font('helvetica', 'B', 13)
    pdf.cell(0, 8, '1. Company Overview', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('helvetica', '', 10)
    pdf.multi_cell(0, 6, f'NovaTech Holdings is an enterprise software and financial analytics provider. In {year}, the company expanded its cloud infrastructure footprint and achieved strong operational milestones across North America and Europe.')
    pdf.ln(4)
    
    pdf.set_font('helvetica', 'B', 13)
    pdf.cell(0, 8, '2. Financial Performance & Income Statement', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('helvetica', '', 10)
    summary_text = (
        f'For the fiscal year {year}, NovaTech reported total Revenue of  (equivalent to  million), '
        f'representing strong business execution. Total Operating Expenses were . '
        f'Gross Profit was recorded at . '
        f'Operating Profit stood at , and Net Profit (Net Income) reached .'
    )
    pdf.multi_cell(0, 6, summary_text)
    pdf.ln(4)

    pdf.set_font('helvetica', 'B', 13)
    pdf.cell(0, 8, '3. Balance Sheet Summary', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('helvetica', '', 10)
    bs_text = (
        f'As of December 31, {year}, Total Assets were  ( million), '
        f'including Current Assets of  and Cash and Cash Equivalents of . '
        f'Total Liabilities were , of which Current Liabilities represented . '
        f'Total Shareholders Equity stood at .'
    )
    pdf.multi_cell(0, 6, bs_text)
    pdf.ln(4)

    # Page 2: Cash Flow, Highlights & Risks
    pdf.add_page()
    pdf.set_font('helvetica', 'B', 13)
    pdf.cell(0, 8, '4. Cash Flow Statement Summary', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('helvetica', '', 10)
    cf_text = (
        f'Operating Cash Flow for {year} was positive at . '
        f'Capital expenditures totaled ,000,000 primarily focused on server modernization. '
        f'Cash and cash equivalents ended the period at .'
    )
    pdf.multi_cell(0, 6, cf_text)
    pdf.ln(4)

    pdf.set_font('helvetica', 'B', 13)
    pdf.cell(0, 8, '5. Financial Highlights', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('helvetica', '', 10)
    highlights = (
        f'- Achieved record annual revenue of  in fiscal year {year}.\n'
        f'- Net profit reached  with expanding operating margins.\n'
        f'- Maintained strong liquidity with cash reserves of .\n'
        f'- Debt-to-equity ratio was maintained at a healthy conservative ratio.'
    )
    pdf.multi_cell(0, 6, highlights)
    pdf.ln(4)

    pdf.set_font('helvetica', 'B', 13)
    pdf.cell(0, 8, '6. Financial Risks and Market Concerns', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('helvetica', '', 10)
    risks = (
        f'Key risks for {year} include foreign exchange rate volatility, macroeconomic inflation impacting client IT budgets, '
        f'and competitive pressures in cloud computing services. Counterparty credit risk remains closely monitored by the audit committee.'
    )
    pdf.multi_cell(0, 6, risks)

    Path(filename).parent.mkdir(parents=True, exist_ok=True)
    pdf.output(filename)
    print(f'Created {filename}')

def create_terminology_pdf(filename):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('helvetica', 'B', 16)
    pdf.cell(0, 10, 'Financial Terminology and KPI Definitions Guide', new_x='LMARGIN', new_y='NEXT', align='C')
    pdf.ln(8)
    
    terms = [
        ('Revenue (Top Line)', 'The total amount of money brought in by a company through sales of goods or services.'),
        ('Net Profit (Bottom Line / Net Income)', 'The amount of money that remains after subtracting all operating costs, taxes, and expenses from total revenue.'),
        ('Gross Profit', 'Revenue minus the Cost of Goods Sold (COGS). Measures production efficiency.'),
        ('Operating Profit (EBIT)', 'Profit realized from business operations before deducting interest and taxes.'),
        ('Total Assets', 'The sum of all current and non-current economic resources owned by the company.'),
        ('Total Liabilities', 'The aggregate debts and obligations owed by the company to outside parties.'),
        ('Shareholders Equity', 'Total Assets minus Total Liabilities; represents the net worth or book value of the enterprise.'),
        ('Current Assets & Current Liabilities', 'Assets expected to be converted to cash within one year versus debts due within one year.'),
        ('Cash and Cash Equivalents', 'Highly liquid assets and treasury instruments immediately available for operational disbursements.')
    ]
    
    for term, definition in terms:
        pdf.set_font('helvetica', 'B', 11)
        pdf.cell(0, 7, term, new_x='LMARGIN', new_y='NEXT')
        pdf.set_font('helvetica', '', 10)
        pdf.multi_cell(0, 5, definition)
        pdf.ln(3)
        
    Path(filename).parent.mkdir(parents=True, exist_ok=True)
    pdf.output(filename)
    print(f'Created {filename}')

def create_kpi_csv(filename):
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
    Path(filename).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(filename, index=False)
    print(f'Created {filename}')

def generate_all_data():
    create_pdf_report(
        2023, 125000000, 80000000, 45000000, 25000000, 15000000,
        600000000, 280000000, 320000000, 210000000, 95000000, 65000000,
        'data/sample_reports/annual_report_2023.pdf'
    )
    create_pdf_report(
        2024, 150000000, 95000000, 55000000, 32000000, 20000000,
        720000000, 310000000, 410000000, 260000000, 110000000, 85000000,
        'data/sample_reports/annual_report_2024.pdf'
    )
    create_terminology_pdf('data/sample_reports/financial_terminology.pdf')
    create_kpi_csv('data/financial_csv/financial_kpi_dataset.csv')
    create_kpi_csv('data/balance_sheet.csv')
    create_pdf_report(
        2024, 150000000, 95000000, 55000000, 32000000, 20000000,
        720000000, 310000000, 410000000, 260000000, 110000000, 85000000,
        'data/annual_report.pdf'
    )

if __name__ == '__main__':
    generate_all_data()
