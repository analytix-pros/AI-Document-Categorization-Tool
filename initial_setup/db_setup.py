# Assuming utils_uuid.py and utils.py are in the same directory
from config.config import *
from ..database.db_models import create_connection
from ..utils.utils_system_specs import *
from ..utils.utils_uuid import derive_uuid
from ..utils.utils import get_utc_datetime


def setup_database():
    conn = create_connection()
    c = conn.cursor()

    # Enable foreign keys
    c.execute("PRAGMA foreign_keys = ON")

    # Create organization table
    c.execute('''
    CREATE TABLE IF NOT EXISTS organization (
        organization_uuid BLOB PRIMARY KEY,
        name TEXT,
        vm_name TEXT,
        vm_hash BLOB UNIQUE,
        is_active INTEGER,
        is_automation_on INTEGER,
        created_datetime TEXT,
        updated_datetime TEXT
    )
    ''')
    c.execute('CREATE INDEX IF NOT EXISTS organization_vm_hash ON organization (vm_hash)')

    # Create user_role table
    c.execute('''
    CREATE TABLE IF NOT EXISTS user_role (
        user_role_uuid BLOB PRIMARY KEY,
        name TEXT UNIQUE,
        description TEXT,
        is_active INTEGER,
        created_datetime TEXT,
        updated_datetime TEXT
    )
    ''')

    # Create user table
    c.execute('''
    CREATE TABLE IF NOT EXISTS user (
        user_uuid BLOB PRIMARY KEY,
        organization_uuid BLOB,
        user_role_uuid BLOB,
        username TEXT UNIQUE,
        pwd TEXT,
        first_name TEXT,
        last_name TEXT,
        email TEXT,
        is_active INTEGER,
        created_datetime TEXT,
        updated_datetime TEXT,
        FOREIGN KEY (organization_uuid) REFERENCES organization (organization_uuid),
        FOREIGN KEY (user_role_uuid) REFERENCES user_role (user_role_uuid)
    )
    ''')
    c.execute('CREATE INDEX IF NOT EXISTS user_organization_uuid ON user (organization_uuid)')
    c.execute('CREATE INDEX IF NOT EXISTS user_role_uuid ON user (user_role_uuid)')

    # Create automation table
    c.execute('''
    CREATE TABLE IF NOT EXISTS automation (
        automation_uuid BLOB PRIMARY KEY,
        organization_uuid BLOB,
        input_directory TEXT,
        output_directory TEXT,
        review_directory TEXT,
        schedule TEXT,
        is_active INTEGER,
        created_datetime TEXT,
        created_by BLOB,
        updated_datetime TEXT,
        updated_by BLOB,
        FOREIGN KEY (organization_uuid) REFERENCES organization (organization_uuid),
        FOREIGN KEY (created_by) REFERENCES user (user_uuid),
        FOREIGN KEY (updated_by) REFERENCES user (user_uuid)
    )
    ''')
    c.execute('CREATE INDEX IF NOT EXISTS automation_organization_uuid ON automation (organization_uuid)')

    # Create ocr_models table
    c.execute('''
    CREATE TABLE IF NOT EXISTS ocr_models (
        ocr_models_uuid BLOB PRIMARY KEY,
        name TEXT,
        default_language TEXT,
        default_dpi INTEGER,
        max_pages INTEGER,
        is_active INTEGER,
        created_datetime TEXT,
        updated_datetime TEXT
    )
    ''')

    # Create llm_models table
    c.execute('''
    CREATE TABLE IF NOT EXISTS llm_models (
        llm_model_uuid BLOB PRIMARY KEY,
        system TEXT,
        name TEXT,
        description TEXT,
        min_ram_gb INTEGER,
        default_timeout INTEGER,
        gpu_required INTEGER,
        gpu_optional INTEGER,
        min_vram_gb INTEGER,
        is_active INTEGER,
        created_datetime TEXT,
        updated_datetime TEXT
    )
    ''')

    # Create stamps table
    c.execute('''
    CREATE TABLE IF NOT EXISTS stamps (
        stamps_uuid BLOB PRIMARY KEY,
        organization_uuid BLOB,
        name TEXT,
        description TEXT,
        keywords TEXT,
        is_active INTEGER,
        created_datetime TEXT,
        created_by BLOB,
        updated_datetime TEXT,
        updated_by BLOB,
        FOREIGN KEY (organization_uuid) REFERENCES organization (organization_uuid),
        FOREIGN KEY (created_by) REFERENCES user (user_uuid),
        FOREIGN KEY (updated_by) REFERENCES user (user_uuid)
    )
    ''')
    c.execute('CREATE INDEX IF NOT EXISTS stamps_organization_uuid ON stamps (organization_uuid)')

    # Create category table
    c.execute('''
    CREATE TABLE IF NOT EXISTS category (
        category_uuid BLOB PRIMARY KEY,
        parent_category_uuid BLOB,
        organization_uuid BLOB,
        name TEXT,
        hierarchy_level INTEGER,
        use_stamps INTEGER,
        stamps_uuid BLOB,
        description TEXT,
        keywords TEXT,
        file_rename_rules TEXT,
        is_active INTEGER,
        created_datetime TEXT,
        created_by BLOB,
        updated_datetime TEXT,
        updated_by BLOB,
        FOREIGN KEY (parent_category_uuid) REFERENCES category (category_uuid),
        FOREIGN KEY (organization_uuid) REFERENCES organization (organization_uuid),
        FOREIGN KEY (stamps_uuid) REFERENCES stamps (stamps_uuid),
        FOREIGN KEY (created_by) REFERENCES user (user_uuid),
        FOREIGN KEY (updated_by) REFERENCES user (user_uuid)
    )
    ''')
    c.execute('CREATE INDEX IF NOT EXISTS category_parent_category_uuid ON category (parent_category_uuid)')
    c.execute('CREATE INDEX IF NOT EXISTS category_organization_uuid ON category (organization_uuid)')
    c.execute('CREATE INDEX IF NOT EXISTS category_stamps_uuid ON category (stamps_uuid)')

    # Create logging table
    c.execute('''
    CREATE TABLE IF NOT EXISTS logging (
        logging_uuid BLOB PRIMARY KEY,
        organization_uuid BLOB,
        user_uuid BLOB,
        page TEXT,
        message TEXT,
        level TEXT,
        created_datetime TEXT,
        created_by BLOB,
        FOREIGN KEY (organization_uuid) REFERENCES organization (organization_uuid),
        FOREIGN KEY (user_uuid) REFERENCES user (user_uuid),
        FOREIGN KEY (created_by) REFERENCES user (user_uuid)
    )
    ''')
    c.execute('CREATE INDEX IF NOT EXISTS logging_organization_uuid ON logging (organization_uuid)')
    c.execute('CREATE INDEX IF NOT EXISTS logging_user_uuid ON logging (user_uuid)')
    c.execute('CREATE INDEX IF NOT EXISTS logging_page ON logging (page)')
    c.execute('CREATE INDEX IF NOT EXISTS logging_level ON logging (level)')

    # Create batch table
    c.execute('''
    CREATE TABLE IF NOT EXISTS batch (
        batch_uuid BLOB PRIMARY KEY,
        organization_uuid BLOB,
        automation_uuid BLOB,
        system_metadata TEXT,
        status TEXT,
        process_time INTEGER,
        created_datetime TEXT,
        created_by BLOB,
        FOREIGN KEY (organization_uuid) REFERENCES organization (organization_uuid),
        FOREIGN KEY (automation_uuid) REFERENCES automation (automation_uuid),
        FOREIGN KEY (created_by) REFERENCES user (user_uuid)
    )
    ''')
    c.execute('CREATE INDEX IF NOT EXISTS batch_organization_uuid ON batch (organization_uuid)')
    c.execute('CREATE INDEX IF NOT EXISTS batch_automation_uuid ON batch (automation_uuid)')

    # Create document table
    c.execute('''
    CREATE TABLE IF NOT EXISTS document (
        document_uuid BLOB PRIMARY KEY,
        organization_uuid BLOB,
        upload_name TEXT,
        upload_folder TEXT,
        pdf BLOB,
        is_active INTEGER,
        created_datetime TEXT,
        created_by BLOB,
        updated_datetime TEXT,
        updated_by BLOB,
        FOREIGN KEY (organization_uuid) REFERENCES organization (organization_uuid),
        FOREIGN KEY (created_by) REFERENCES user (user_uuid),
        FOREIGN KEY (updated_by) REFERENCES user (user_uuid)
    )
    ''')
    c.execute('CREATE INDEX IF NOT EXISTS document_organization_uuid ON document (organization_uuid)')

    # Create document_category table
    c.execute('''
    CREATE TABLE IF NOT EXISTS document_category (
        document_category_uuid BLOB PRIMARY KEY,
        organization_uuid BLOB,
        document_uuid BLOB,
        category_uuid BLOB,
        stamps_uuid BLOB,
        category_confidence REAL,
        all_category_confidence TEXT,
        ocr_text TEXT,
        ocr_text_confidence TEXT,
        override_category_uuid BLOB,
        override_context TEXT,
        is_active INTEGER,
        created_datetime TEXT,
        created_by BLOB,
        updated_datetime TEXT,
        updated_by BLOB,
        FOREIGN KEY (organization_uuid) REFERENCES organization (organization_uuid),
        FOREIGN KEY (document_uuid) REFERENCES document (document_uuid),
        FOREIGN KEY (category_uuid) REFERENCES category (category_uuid),
        FOREIGN KEY (stamps_uuid) REFERENCES stamps (stamps_uuid),
        FOREIGN KEY (override_category_uuid) REFERENCES category (category_uuid),
        FOREIGN KEY (created_by) REFERENCES user (user_uuid),
        FOREIGN KEY (updated_by) REFERENCES user (user_uuid)
    )
    ''')
    c.execute('CREATE INDEX IF NOT EXISTS document_category_organization_uuid ON document_category (organization_uuid)')
    c.execute('CREATE INDEX IF NOT EXISTS document_category_document_uuid ON document_category (document_uuid)')
    c.execute('CREATE INDEX IF NOT EXISTS document_category_category_uuid ON document_category (category_uuid)')
    c.execute('CREATE INDEX IF NOT EXISTS document_category_stamps_uuid ON document_category (stamps_uuid)')
    c.execute('CREATE INDEX IF NOT EXISTS document_category_override_category_uuid ON document_category (override_category_uuid)')

    conn.commit()

    # Insert sample data if tables are empty
    now = get_utc_datetime()

    # Check if organization is empty
    c.execute("SELECT COUNT(*) FROM organization")
    if c.fetchone()[0] == 0:
        org_name = 'Local Testing - CS'
        org_uuid = derive_uuid(org_name)
        vm_name = get_hostname()
        vm_hash = derive_uuid(get_hostname())
        c.execute('''
        INSERT INTO organization (organization_uuid, name, vm_name, vm_hash, is_active, is_automation_on, created_datetime, updated_datetime)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (org_uuid, org_name, vm_name, vm_hash, 1, 0, now, now))

    # user_role
    c.execute("SELECT COUNT(*) FROM user_role")
    if c.fetchone()[0] == 0:
        role_uuid = derive_uuid('admin')
        c.execute('''
        INSERT INTO user_role (user_role_uuid, name, description, is_active, created_datetime, updated_datetime)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (role_uuid, 'admin', 'Access to everything and all organizations\' data/settings', 1, now, now))

    # users
    c.execute("SELECT COUNT(*) FROM user")
    if c.fetchone()[0] == 0:

        # Cameron
        user_cameron = 'cameron'
        user_cameron_uuid = derive_uuid(user_cameron)
        pwd_cameron = 'da3ba40c-1af9-5704-8dfb-9b1571aa6ae4'
        c.execute('''
        INSERT INTO user (user_uuid, organization_uuid, user_role_uuid, username, pwd, first_name, last_name, email, is_active, created_datetime, updated_datetime)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_cameron_uuid, None, role_uuid, user_cameron, pwd_cameron, 'Cameron', 'Stroup', 'cameronstroup@analytix-pros.com', 1, now, now))

        # Bryan
        user_bryan = 'bryan'
        user_bryan_uuid = derive_uuid(user_bryan)
        pwd_bryan = '9eeb22a2-420f-5945-a4de-d0a382f0eb4e'
        c.execute('''
        INSERT INTO user (user_uuid, organization_uuid, user_role_uuid, username, pwd, first_name, last_name, email, is_active, created_datetime, updated_datetime)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_bryan_uuid, None, role_uuid, user_bryan, pwd_bryan, 'Bryan', 'Camaglia', 'bcamaglia@cmaanalytics.com', 1, now, now))

    # ocr_models
    c.execute("SELECT COUNT(*) FROM ocr_models")
    if c.fetchone()[0] == 0:

        ocr_models = [ 
            ['Tesseract', 'English', 400, 10],
            ['EasyOCR', 'English', 500, 15],
            ['PaddleOCR', 'English', 550, 20]
        ]
        
        for i in ocr_models:
            c.execute('''
            INSERT INTO ocr_models (ocr_models_uuid, name, default_language, default_dpi, max_pages, is_active, created_datetime, updated_datetime)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (derive_uuid(i[0]), i[0], i[1], i[2], i[3], 1, now, now))


    # llm_models
    c.execute("SELECT COUNT(*) FROM llm_models")
    if c.fetchone()[0] == 0:

        llm_models = [
            ['granite3.2-vision', 'Ollam', 'Best for scanned legal PDFs with tables/forms. Extracts text and categorizes (e.g., invoice, notice) with high accuracy. Ideal for low-resource machines (4-8GB VRAM).', 8, 300, 0, 1, 4],
            ['llava:7b', 'Ollama', 'Excels at text recognition from scans, including handwritten mail. Classifies complex documents (e.g., disputes, proofs) with reasoning. Needs 8-16GB VRAM. 7 billion parameters', 0, 60, 1, 0, 8],
            ['llava:13b', 'Ollama', 'Excels at text recognition from scans, including handwritten mail. Classifies complex documents (e.g., disputes, proofs) with reasoning. Needs 8-16GB VRAM. 13 billion parameters', 0, 60, 1, 0, 16],
            ['qwen2-vl:7b', 'Ollama', 'Strong for multi-page forms and multilingual mail. Fast categorization of legal documents (e.g., demands, filings). Requires 8-12GB VRAM.', 0, 60, 1, 0, 8],
            ['mistral', 'Ollama', 'Efficient for text-based classification after OCR extraction. Ideal for clean, structured legal text (e.g., summons, notices). Runs on 4-8GB RAM.', 4, 60, 0, 0, 0]
        ]

        for i in llm_models:
            c.execute('''
            INSERT INTO llm_models (llm_model_uuid, system, name, description, min_ram_gb, default_timeout, gpu_required, gpu_optional, min_vram_gb, is_active, created_datetime, updated_datetime)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (derive_uuid(i[0]), i[1], i[0], i[2], i[3], i[4], i[5], i[6], i[7], 1, now, now))

    # stamps
    c.execute("SELECT COUNT(*) FROM stamps")
    if c.fetchone()[0] == 0:

        stamps = [
            ['FILED', "['filed', 'file stamped']"],
            ['CERTIFIED', "['certified', 'certified copy', 'certification']"],
            ['RECORDED', "['recorded', 'recording']"],
            ['EXEMPLIFIED', "['exemplified']"],
            ['SERVED', "['served', 'proof of service']"]
        ]

        for i in stamps:
            c.execute('''
            INSERT INTO stamps (stamps_uuid, organization_uuid, name, description, keywords, is_active, created_datetime, created_by, updated_datetime, updated_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (derive_uuid(i[0]), org_uuid, i[0], '', i[1], 1, now, user_cameron_uuid, now, user_cameron_uuid))


    conn.commit()
    conn.close()



try:
    if os.path.exists(FULL_DATABASE_FILE_PATH):
        pass
    else:
        setup_database()
except Exception as e:
    print(f"An unexpected error occurred: {e}")
setup_database()