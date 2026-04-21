import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.db import connection

def create_combo_adjust_tables():
    cursor = connection.cursor()
    
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recipe_combo_adjust_result (
                plan_id INT AUTO_INCREMENT PRIMARY KEY,
                snapshot_id VARCHAR(100),
                recipe_id VARCHAR(100),
                target_canonical_id VARCHAR(100),
                candidate_canonical_id VARCHAR(100),
                repair_canonical_id VARCHAR(100),
                repair_role VARCHAR(100),
                repair_factor FLOAT DEFAULT 1.0,
                old_sqe_total FLOAT,
                single_sqe_total FLOAT,
                combo_sqe_total FLOAT,
                delta_sqe_single FLOAT,
                delta_sqe_combo FLOAT,
                delta_synergy_combo FLOAT,
                delta_conflict_combo FLOAT,
                delta_balance_combo FLOAT,
                accept_flag BOOLEAN DEFAULT FALSE,
                reason_code VARCHAR(100),
                explanation TEXT,
                plan_json JSON,
                rank_no INT,
                model_version VARCHAR(100),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_recipe_id_snapshot_id (recipe_id, snapshot_id),
                INDEX idx_recipe_id_target_canonical_id (recipe_id, target_canonical_id),
                INDEX idx_recipe_id_accept_flag (recipe_id, accept_flag),
                INDEX idx_rank_no (rank_no),
                INDEX idx_recipe_id_rank_no (recipe_id, rank_no)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recipe_combo_adjust_step (
                step_id INT AUTO_INCREMENT PRIMARY KEY,
                plan_id INT,
                step_no INT,
                op_type VARCHAR(50),
                target_ingredient VARCHAR(255),
                target_canonical VARCHAR(100),
                candidate_ingredient VARCHAR(255),
                candidate_canonical VARCHAR(100),
                amount_factor FLOAT,
                role_info VARCHAR(100),
                before_sqe_total FLOAT,
                after_sqe_total FLOAT,
                delta_sqe FLOAT,
                note TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_plan_id_step_no (plan_id, step_no),
                FOREIGN KEY (plan_id) REFERENCES recipe_combo_adjust_result(plan_id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)
        
        connection.commit()
        print("Tables created successfully!")
        
    except Exception as e:
        connection.rollback()
        print(f"Error creating tables: {e}")
    finally:
        cursor.close()

if __name__ == "__main__":
    create_combo_adjust_tables()