-- Create the banking database
CREATE DATABASE banking_system;
USE banking_system;

-- Table 1: Banks
CREATE TABLE banks (
    bank_id INT PRIMARY KEY AUTO_INCREMENT,
    bank_name VARCHAR(100) NOT NULL,
    bank_code VARCHAR(10) UNIQUE NOT NULL,
    swift_code VARCHAR(11),
    headquarters_address VARCHAR(255),
    phone VARCHAR(20),
    email VARCHAR(100),
    established_date DATE,
    total_assets DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Table 2: Branches
CREATE TABLE branches (
    branch_id INT PRIMARY KEY AUTO_INCREMENT,
    bank_id INT NOT NULL,
    branch_name VARCHAR(100) NOT NULL,
    branch_code VARCHAR(10) NOT NULL,
    address VARCHAR(255),
    city VARCHAR(50),
    state VARCHAR(50),
    zip_code VARCHAR(10),
    phone VARCHAR(20),
    manager_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bank_id) REFERENCES banks(bank_id) ON DELETE CASCADE,
    UNIQUE KEY unique_branch_code (bank_id, branch_code)
);

-- Table 3: Users/Customers
CREATE TABLE users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    date_of_birth DATE,
    ssn VARCHAR(11) UNIQUE,
    address VARCHAR(255),
    city VARCHAR(50),
    state VARCHAR(50),
    zip_code VARCHAR(10),
    occupation VARCHAR(100),
    annual_income DECIMAL(12,2),
    credit_score INT,
    registration_date DATE DEFAULT (CURDATE()),
    status ENUM('active', 'inactive', 'suspended') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Table 4: Account Types
CREATE TABLE account_types (
    account_type_id INT PRIMARY KEY AUTO_INCREMENT,
    type_name VARCHAR(50) NOT NULL,
    description TEXT,
    minimum_balance DECIMAL(10,2) DEFAULT 0.00,
    interest_rate DECIMAL(5,4) DEFAULT 0.0000,
    monthly_fee DECIMAL(8,2) DEFAULT 0.00,
    transaction_limit INT DEFAULT 0,
    overdraft_allowed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table 5: Accounts
CREATE TABLE accounts (
    account_id INT PRIMARY KEY AUTO_INCREMENT,
    account_number VARCHAR(20) UNIQUE NOT NULL,
    user_id INT NOT NULL,
    branch_id INT NOT NULL,
    account_type_id INT NOT NULL,
    balance DECIMAL(15,2) DEFAULT 0.00,
    available_balance DECIMAL(15,2) DEFAULT 0.00,
    overdraft_limit DECIMAL(10,2) DEFAULT 0.00,
    status ENUM('active', 'closed', 'frozen', 'suspended') DEFAULT 'active',
    opening_date DATE DEFAULT (CURDATE()),
    closing_date DATE NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (branch_id) REFERENCES branches(branch_id),
    FOREIGN KEY (account_type_id) REFERENCES account_types(account_type_id)
);

-- Table 6: Transaction Types
CREATE TABLE transaction_types (
    transaction_type_id INT PRIMARY KEY AUTO_INCREMENT,
    type_name VARCHAR(50) NOT NULL,
    description TEXT,
    is_debit BOOLEAN NOT NULL,
    fee DECIMAL(8,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table 7: Transactions
CREATE TABLE transactions (
    transaction_id INT PRIMARY KEY AUTO_INCREMENT,
    transaction_number VARCHAR(50) UNIQUE NOT NULL,
    account_id INT NOT NULL,
    transaction_type_id INT NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    balance_after DECIMAL(15,2) NOT NULL,
    description TEXT,
    reference_number VARCHAR(100),
    processed_by INT,
    transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    status ENUM('pending', 'completed', 'failed', 'cancelled') DEFAULT 'completed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES accounts(account_id) ON DELETE CASCADE,
    FOREIGN KEY (transaction_type_id) REFERENCES transaction_types(transaction_type_id),
    FOREIGN KEY (processed_by) REFERENCES users(user_id)
);

-- Table 8: Loans
CREATE TABLE loans (
    loan_id INT PRIMARY KEY AUTO_INCREMENT,
    loan_number VARCHAR(20) UNIQUE NOT NULL,
    user_id INT NOT NULL,
    branch_id INT NOT NULL,
    loan_type ENUM('personal', 'mortgage', 'auto', 'business', 'student') NOT NULL,
    principal_amount DECIMAL(15,2) NOT NULL,
    interest_rate DECIMAL(5,4) NOT NULL,
    term_months INT NOT NULL,
    monthly_payment DECIMAL(10,2) NOT NULL,
    outstanding_balance DECIMAL(15,2) NOT NULL,
    status ENUM('active', 'paid_off', 'default', 'closed') DEFAULT 'active',
    disbursement_date DATE,
    maturity_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (branch_id) REFERENCES branches(branch_id)
);

-- Table 9: Loan Payments
CREATE TABLE loan_payments (
    payment_id INT PRIMARY KEY AUTO_INCREMENT,
    loan_id INT NOT NULL,
    payment_number VARCHAR(50) UNIQUE NOT NULL,
    payment_amount DECIMAL(10,2) NOT NULL,
    principal_amount DECIMAL(10,2) NOT NULL,
    interest_amount DECIMAL(10,2) NOT NULL,
    remaining_balance DECIMAL(15,2) NOT NULL,
    payment_date DATE NOT NULL,
    due_date DATE NOT NULL,
    status ENUM('paid', 'overdue', 'partial') DEFAULT 'paid',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (loan_id) REFERENCES loans(loan_id) ON DELETE CASCADE
);

-- Table 10: Cards
CREATE TABLE cards (
    card_id INT PRIMARY KEY AUTO_INCREMENT,
    card_number VARCHAR(19) UNIQUE NOT NULL,
    account_id INT NOT NULL,
    card_type ENUM('debit', 'credit', 'prepaid') NOT NULL,
    card_status ENUM('active', 'blocked', 'expired', 'cancelled') DEFAULT 'active',
    issue_date DATE DEFAULT (CURDATE()),
    expiry_date DATE NOT NULL,
    credit_limit DECIMAL(10,2) DEFAULT 0.00,
    available_credit DECIMAL(10,2) DEFAULT 0.00,
    pin_hash VARCHAR(255),
    cvv VARCHAR(4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES accounts(account_id) ON DELETE CASCADE
);

-- Insert sample data

-- Insert Banks
INSERT INTO banks (bank_name, bank_code, swift_code, headquarters_address, phone, email, established_date, total_assets) VALUES
('First National Bank', 'FNB001', 'FNBKUS33XXX', '123 Main St, New York, NY 10001', '555-0101', 'info@fnb.com', '1985-03-15', 50000000000.00),
('City Commercial Bank', 'CCB002', 'CCBKUS44XXX', '456 Broadway, Los Angeles, CA 90210', '555-0102', 'contact@ccb.com', '1992-07-22', 35000000000.00),
('Regional Trust Bank', 'RTB003', 'RTBKUS55XXX', '789 Oak Ave, Chicago, IL 60601', '555-0103', 'support@rtb.com', '1978-11-08', 28000000000.00),
('Metropolitan Bank', 'MET004', 'METBUS66XXX', '321 Pine St, Houston, TX 77001', '555-0104', 'help@metbank.com', '1988-05-12', 42000000000.00),
('Community First Bank', 'CFB005', 'CFBKUS77XXX', '654 Elm St, Phoenix, AZ 85001', '555-0105', 'service@cfb.com', '1995-09-30', 18000000000.00),
('United Federal Bank', 'UFB006', 'UFBKUS88XXX', '987 Cedar Rd, Philadelphia, PA 19101', '555-0106', 'info@ufb.com', '1982-01-18', 38000000000.00),
('Liberty Savings Bank', 'LSB007', 'LSBKUS99XXX', '147 Maple Dr, San Antonio, TX 78201', '555-0107', 'contact@lsb.com', '1990-12-03', 22000000000.00),
('American Trust Bank', 'ATB008', 'ATBKUS11XXX', '258 Birch Ln, San Diego, CA 92101', '555-0108', 'support@atb.com', '1987-06-25', 31000000000.00),
('National Commerce Bank', 'NCB009', 'NCBKUS22XXX', '369 Spruce St, Dallas, TX 75201', '555-0109', 'help@ncb.com', '1993-04-14', 26000000000.00),
('Pacific Bank & Trust', 'PBT010', 'PBTUS33XXX', '741 Willow Way, San Jose, CA 95101', '555-0110', 'service@pbt.com', '1991-08-07', 33000000000.00);

-- Insert Branches
INSERT INTO branches (bank_id, branch_name, branch_code, address, city, state, zip_code, phone, manager_name) VALUES
(1, 'Downtown Branch', 'DTN001', '123 Main St', 'New York', 'NY', '10001', '555-1001', 'John Smith'),
(1, 'Midtown Branch', 'MDT001', '456 5th Ave', 'New York', 'NY', '10017', '555-1002', 'Sarah Johnson'),
(2, 'Beverly Hills Branch', 'BVH001', '789 Rodeo Dr', 'Beverly Hills', 'CA', '90210', '555-2001', 'Michael Brown'),
(2, 'Santa Monica Branch', 'SMC001', '321 Ocean Blvd', 'Santa Monica', 'CA', '90401', '555-2002', 'Emily Davis'),
(3, 'Loop Branch', 'LOP001', '654 LaSalle St', 'Chicago', 'IL', '60601', '555-3001', 'David Wilson'),
(3, 'North Side Branch', 'NTH001', '987 Clark St', 'Chicago', 'IL', '60614', '555-3002', 'Lisa Anderson'),
(4, 'Galleria Branch', 'GAL001', '147 Post Oak Blvd', 'Houston', 'TX', '77056', '555-4001', 'Robert Miller'),
(4, 'Heights Branch', 'HGT001', '258 19th St', 'Houston', 'TX', '77008', '555-4002', 'Jennifer Taylor'),
(5, 'Central Phoenix Branch', 'CPX001', '369 Central Ave', 'Phoenix', 'AZ', '85004', '555-5001', 'Christopher Lee'),
(5, 'Scottsdale Branch', 'SCT001', '741 Scottsdale Rd', 'Scottsdale', 'AZ', '85251', '555-5002', 'Amanda White');

-- Insert Users
INSERT INTO users (first_name, last_name, email, phone, date_of_birth, ssn, address, city, state, zip_code, occupation, annual_income, credit_score) VALUES
('James', 'Wilson', 'james.wilson@email.com', '555-1111', '1985-03-15', '123-45-6789', '123 Oak St', 'New York', 'NY', '10001', 'Software Engineer', 95000.00, 750),
('Maria', 'Garcia', 'maria.garcia@email.com', '555-2222', '1990-07-22', '234-56-7890', '456 Pine Ave', 'Los Angeles', 'CA', '90210', 'Marketing Manager', 78000.00, 720),
('Robert', 'Johnson', 'robert.johnson@email.com', '555-3333', '1978-11-08', '345-67-8901', '789 Elm Dr', 'Chicago', 'IL', '60601', 'Accountant', 68000.00, 680),
('Jennifer', 'Brown', 'jennifer.brown@email.com', '555-4444', '1992-05-12', '456-78-9012', '321 Maple Ln', 'Houston', 'TX', '77001', 'Nurse', 72000.00, 700),
('Michael', 'Davis', 'michael.davis@email.com', '555-5555', '1988-09-30', '567-89-0123', '654 Cedar Rd', 'Phoenix', 'AZ', '85001', 'Teacher', 52000.00, 690),
('Lisa', 'Miller', 'lisa.miller@email.com', '555-6666', '1995-01-18', '678-90-1234', '987 Birch St', 'Philadelphia', 'PA', '19101', 'Graphic Designer', 58000.00, 710),
('David', 'Wilson', 'david.wilson@email.com', '555-7777', '1983-12-03', '789-01-2345', '147 Spruce Ave', 'San Antonio', 'TX', '78201', 'Sales Manager', 82000.00, 730),
('Sarah', 'Moore', 'sarah.moore@email.com', '555-8888', '1987-06-25', '890-12-3456', '258 Willow Dr', 'San Diego', 'CA', '92101', 'Physical Therapist', 75000.00, 740),
('Christopher', 'Taylor', 'chris.taylor@email.com', '555-9999', '1991-04-14', '901-23-4567', '369 Poplar Ln', 'Dallas', 'TX', '75201', 'Engineer', 88000.00, 760),
('Amanda', 'Anderson', 'amanda.anderson@email.com', '555-0000', '1989-08-07', '012-34-5678', '741 Ash Rd', 'San Jose', 'CA', '95101', 'Project Manager', 92000.00, 780);

-- Insert Account Types
INSERT INTO account_types (type_name, description, minimum_balance, interest_rate, monthly_fee, transaction_limit, overdraft_allowed) VALUES
('Checking', 'Standard checking account for daily transactions', 25.00, 0.0100, 10.00, 0, TRUE),
('Savings', 'High-yield savings account', 100.00, 2.5000, 5.00, 6, FALSE),
('Premium Checking', 'Premium checking with higher limits', 1000.00, 0.5000, 25.00, 0, TRUE),
('Business Checking', 'Business checking account', 500.00, 0.2500, 20.00, 0, TRUE),
('Money Market', 'High-interest money market account', 2500.00, 3.0000, 15.00, 10, FALSE),
('CD Account', 'Certificate of deposit account', 1000.00, 4.0000, 0.00, 0, FALSE),
('Student Checking', 'Free checking for students', 0.00, 0.0000, 0.00, 0, FALSE),
('Senior Savings', 'Special savings for senior citizens', 50.00, 2.7500, 0.00, 8, FALSE),
('Investment Account', 'Investment and brokerage account', 5000.00, 0.0000, 50.00, 0, FALSE),
('IRA Account', 'Individual Retirement Account', 1000.00, 3.5000, 10.00, 2, FALSE);

-- Insert Accounts
INSERT INTO accounts (account_number, user_id, branch_id, account_type_id, balance, available_balance, overdraft_limit) VALUES
('1001234567890', 1, 1, 1, 2500.75, 2500.75, 500.00),
('1001234567891', 1, 1, 2, 15000.00, 15000.00, 0.00),
('2001234567890', 2, 3, 1, 1800.25, 1800.25, 300.00),
('2001234567891', 2, 3, 5, 25000.50, 25000.50, 0.00),
('3001234567890', 3, 5, 1, 950.00, 950.00, 200.00),
('3001234567891', 3, 5, 2, 8500.75, 8500.75, 0.00),
('4001234567890', 4, 7, 3, 5200.00, 5200.00, 1000.00),
('4001234567891', 4, 7, 2, 12000.25, 12000.25, 0.00),
('5001234567890', 5, 9, 7, 750.50, 750.50, 0.00),
('5001234567891', 5, 9, 2, 3200.00, 3200.00, 0.00);

-- Insert Transaction Types
INSERT INTO transaction_types (type_name, description, is_debit, fee) VALUES
('Deposit', 'Cash or check deposit', FALSE, 0.00),
('Withdrawal', 'Cash withdrawal', TRUE, 2.50),
('Transfer In', 'Incoming transfer', FALSE, 0.00),
('Transfer Out', 'Outgoing transfer', TRUE, 5.00),
('Purchase', 'Debit card purchase', TRUE, 0.00),
('ATM Withdrawal', 'ATM cash withdrawal', TRUE, 3.00),
('Direct Deposit', 'Payroll or benefits deposit', FALSE, 0.00),
('Bill Payment', 'Automatic bill payment', TRUE, 1.00),
('Interest Payment', 'Interest earned', FALSE, 0.00),
('Monthly Fee', 'Monthly account maintenance fee', TRUE, 0.00);

-- Insert Transactions
INSERT INTO transactions (transaction_number, account_id, transaction_type_id, amount, balance_after, description, reference_number) VALUES
('TXN001', 1, 7, 3200.00, 3200.00, 'Salary deposit', 'DD2024001'),
('TXN002', 1, 5, 45.50, 3154.50, 'Grocery store purchase', 'POS2024001'),
('TXN003', 1, 6, 100.00, 3051.50, 'ATM withdrawal', 'ATM2024001'),
('TXN004', 2, 1, 500.00, 2000.00, 'Cash deposit', 'DEP2024001'),
('TXN005', 2, 8, 125.75, 1874.25, 'Electric bill payment', 'BP2024001'),
('TXN006', 3, 7, 2800.00, 2800.00, 'Salary deposit', 'DD2024002'),
('TXN007', 3, 5, 32.25, 2767.75, 'Coffee shop purchase', 'POS2024002'),
('TXN008', 4, 1, 1000.00, 6200.00, 'Check deposit', 'CHK2024001'),
('TXN009', 4, 4, 500.00, 5700.00, 'Transfer to savings', 'TRF2024001'),
('TXN010', 5, 7, 1200.00, 1200.00, 'Part-time job deposit', 'DD2024003');

-- Insert Loans
INSERT INTO loans (loan_number, user_id, branch_id, loan_type, principal_amount, interest_rate, term_months, monthly_payment, outstanding_balance, disbursement_date, maturity_date) VALUES
('LN2024001', 1, 1, 'auto', 25000.00, 4.5000, 60, 465.51, 22500.00, '2024-01-15', '2029-01-15'),
('LN2024002', 2, 3, 'personal', 15000.00, 8.2500, 36, 473.16, 12000.00, '2024-02-01', '2027-02-01'),
('LN2024003', 3, 5, 'mortgage', 250000.00, 3.7500, 360, 1147.29, 240000.00, '2024-01-01', '2054-01-01'),
('LN2024004', 4, 7, 'student', 35000.00, 5.2500, 120, 375.85, 30000.00, '2023-09-01', '2033-09-01'),
('LN2024005', 5, 9, 'personal', 8000.00, 9.7500, 24, 367.89, 6000.00, '2024-03-01', '2026-03-01'),
('LN2024006', 6, 2, 'auto', 18000.00, 4.2500, 48, 408.52, 15000.00, '2024-02-15', '2028-02-15'),
('LN2024007', 7, 4, 'business', 75000.00, 6.5000, 84, 1078.95, 65000.00, '2024-01-10', '2031-01-10'),
('LN2024008', 8, 6, 'mortgage', 180000.00, 3.8750, 360, 845.78, 175000.00, '2023-12-01', '2053-12-01'),
('LN2024009', 9, 8, 'auto', 32000.00, 4.7500, 72, 485.32, 28000.00, '2024-01-20', '2030-01-20'),
('LN2024010', 10, 10, 'personal', 12000.00, 7.9500, 48, 293.71, 9500.00, '2024-02-10', '2028-02-10');

-- Insert Loan Payments
INSERT INTO loan_payments (loan_id, payment_number, payment_amount, principal_amount, interest_amount, remaining_balance, payment_date, due_date) VALUES
(1, 'PAY001-01', 465.51, 371.26, 94.25, 24628.74, '2024-02-15', '2024-02-15'),
(1, 'PAY001-02', 465.51, 372.65, 92.86, 24256.09, '2024-03-15', '2024-03-15'),
(2, 'PAY002-01', 473.16, 370.41, 102.75, 14629.59, '2024-03-01', '2024-03-01'),
(2, 'PAY002-02', 473.16, 372.96, 100.20, 14256.63, '2024-04-01', '2024-04-01'),
(3, 'PAY003-01', 1147.29, 366.04, 781.25, 249633.96, '2024-02-01', '2024-02-01'),
(3, 'PAY003-02', 1147.29, 367.18, 780.11, 249266.78, '2024-03-01', '2024-03-01'),
(4, 'PAY004-01', 375.85, 223.60, 152.25, 34776.40, '2024-01-01', '2024-01-01'),
(4, 'PAY004-02', 375.85, 224.58, 151.27, 34551.82, '2024-02-01', '2024-02-01'),
(5, 'PAY005-01', 367.89, 303.39, 64.50, 7696.61, '2024-04-01', '2024-04-01'),
(10, 'PAY010-01', 293.71, 214.21, 79.50, 11785.79, '2024-03-10', '2024-03-10');

-- Insert Cards
INSERT INTO cards (card_number, account_id, card_type, expiry_date, credit_limit, available_credit, cvv) VALUES
('4532-1234-5678-9012', 1, 'debit', '2027-12-31', 0.00, 0.00, '123'),
('5412-3456-7890-1234', 1, 'credit', '2028-06-30', 5000.00, 4200.00, '456'),
('4716-2345-6789-0123', 2, 'debit', '2027-11-30', 0.00, 0.00, '789'),
('5523-4567-8901-2345', 3, 'debit', '2028-01-31', 0.00, 0.00, '321'),
('4829-5678-9012-3456', 4, 'credit', '2027-09-30', 10000.00, 8500.00, '654'),
('5434-6789-0123-4567', 4, 'debit', '2028-03-31', 0.00, 0.00, '987'),
('4175-7890-1234-5678', 5, 'debit', '2027-10-31', 0.00, 0.00, '147'),
('5545-8901-2345-6789', 6, 'credit', '2028-05-31', 3000.00, 2750.00, '258'),
('4362-9012-3456-7890', 7, 'debit', '2027-08-31', 0.00, 0.00, '369'),
('5656-0123-4567-8901', 8, 'credit', '2028-02-29', 7500.00, 6900.00, '741');

-- Create indexes for better performance on common queries
CREATE INDEX idx_accounts_user_id ON accounts(user_id);
CREATE INDEX idx_transactions_account_id ON transactions(account_id);
CREATE INDEX idx_transactions_date ON transactions(transaction_date);
CREATE INDEX idx_loans_user_id ON loans(user_id);
CREATE INDEX idx_loan_payments_loan_id ON loan_payments(loan_id);
CREATE INDEX idx_cards_account_id ON cards(account_id);
CREATE INDEX idx_branches_bank_id ON branches(bank_id);
