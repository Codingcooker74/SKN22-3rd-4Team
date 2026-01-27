-- Supabase Database Schema
-- Last Updated: 2026-01-27

-- 1. Companies Table
CREATE TABLE public.companies (
    id uuid NOT NULL DEFAULT uuid_generate_v4 (),
    ticker text NOT NULL UNIQUE,
    company_name text NOT NULL,
    cik text,
    industry text,
    sector text,
    description text,
    logo_url text,
    market_cap numeric,
    employees integer,
    exchange text,
    website text,
    created_at timestamp
    with
        time zone DEFAULT now (),
        founded_year integer,
        headquarters text,
        CONSTRAINT companies_pkey PRIMARY KEY (id)
);

-- 2. Annual Reports Table
CREATE TABLE public.annual_reports (
    id uuid NOT NULL DEFAULT uuid_generate_v4 (),
    company_id uuid,
    fiscal_year integer NOT NULL,
    period_ended date,
    revenue numeric,
    cost_of_revenue numeric,
    gross_profit numeric,
    operating_income numeric,
    net_income numeric,
    eps numeric,
    total_assets numeric,
    total_liabilities numeric,
    stockholders_equity numeric,
    operating_cash_flow numeric,
    investing_cash_flow numeric,
    financing_cash_flow numeric,
    profit_margin numeric,
    roe numeric,
    roa numeric,
    debt_to_equity numeric,
    current_ratio numeric,
    created_at timestamp
    with
        time zone DEFAULT now (),
        updated_at timestamp
    with
        time zone DEFAULT now (),
        CONSTRAINT annual_reports_pkey PRIMARY KEY (id),
        CONSTRAINT annual_reports_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies (id)
);

-- 3. Quarterly Reports Table
CREATE TABLE public.quarterly_reports (
    id uuid NOT NULL DEFAULT uuid_generate_v4 (),
    company_id uuid,
    fiscal_year integer NOT NULL,
    fiscal_quarter integer NOT NULL,
    period_ended date NOT NULL,
    revenue numeric,
    gross_profit numeric,
    operating_income numeric,
    net_income numeric,
    eps numeric,
    operating_cash_flow numeric,
    created_at timestamp
    with
        time zone DEFAULT now (),
        CONSTRAINT quarterly_reports_pkey PRIMARY KEY (id),
        CONSTRAINT quarterly_reports_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies (id)
);

-- 4. Stock Prices Table
CREATE TABLE public.stock_prices (
    id uuid NOT NULL DEFAULT uuid_generate_v4 (),
    company_id uuid,
    price_date date NOT NULL,
    open_price numeric,
    high_price numeric,
    low_price numeric,
    close_price numeric,
    adjusted_close numeric,
    volume bigint,
    market_cap numeric,
    pe_ratio numeric,
    pb_ratio numeric,
    ps_ratio numeric,
    created_at timestamp
    with
        time zone DEFAULT now (),
        CONSTRAINT stock_prices_pkey PRIMARY KEY (id),
        CONSTRAINT stock_prices_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies (id)
);

-- 5. Company Relationships Table (GraphRAG)
CREATE TABLE public.company_relationships (
    id uuid NOT NULL DEFAULT uuid_generate_v4 (),
    source_company text NOT NULL,
    source_ticker text,
    target_company text NOT NULL,
    target_ticker text,
    relationship_type text NOT NULL,
    confidence numeric DEFAULT 0.5,
    extracted_from text,
    filing_date date,
    created_at timestamp
    with
        time zone DEFAULT now (),
        CONSTRAINT company_relationships_pkey PRIMARY KEY (id)
);

-- 6. Document Sections Table
CREATE TABLE public.document_sections (
    id uuid NOT NULL DEFAULT uuid_generate_v4 (),
    company_id uuid,
    content text NOT NULL,
    section_name text,
    report_type text,
    report_date date,
    metadata jsonb,
    created_at timestamp
    with
        time zone DEFAULT now (),
        ticker text,
        filing_date date,
        CONSTRAINT document_sections_pkey PRIMARY KEY (id),
        CONSTRAINT document_sections_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies (id)
);

-- 7. Documents Table (Vector Store)
CREATE TABLE public.documents (
    id uuid NOT NULL,
    content text,
    metadata jsonb,
    embedding USER - DEFINED, -- pgvector type
    CONSTRAINT documents_pkey PRIMARY KEY (id)
);