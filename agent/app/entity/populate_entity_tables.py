#!/usr/bin/env python3
"""
填充实体表数据

将entity_lexicon.json和entity_patterns.json中的数据填充到entities和aliases表中
"""

import json
import mysql.connector
from mysql.connector import errors
from datetime import datetime

# 导入配置
from app.config import settings

# 数据库连接配置
DB_CONFIG = {
    'host': settings.MYSQL_HOST,
    'user': settings.MYSQL_USER,
    'password': settings.MYSQL_PASSWORD,
    'database': settings.MYSQL_DATABASE,
    'port': settings.MYSQL_PORT
}

def get_db_connection():
    """获取数据库连接"""
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except errors.ProgrammingError as e:
        raise

def create_entity_tables():
    """创建实体相关的表结构"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 创建entities表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS entities (
            entity_id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL UNIQUE,
            label VARCHAR(50) NOT NULL,
            normalized_name VARCHAR(255) NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_entity_label (label),
            INDEX idx_entity_normalized (normalized_name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')
        
        # 创建aliases表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS aliases (
            alias_id INT AUTO_INCREMENT PRIMARY KEY,
            entity_id INT NOT NULL,
            alias_name VARCHAR(255) NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (entity_id) REFERENCES entities(entity_id),
            INDEX idx_alias_entity (entity_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')
        
        conn.commit()
        print("Entity tables created successfully!")
    except Exception as e:
        print(f"Error creating entity tables: {str(e)}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def populate_entities_from_lexicon():
    """从entity_lexicon.json填充entities和aliases表"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 读取entity_lexicon.json文件
        with open('entity_lexicon.json', 'r', encoding='utf-8') as f:
            lexicon_data = json.load(f)
        
        # 处理每个类别
        for label, entities in lexicon_data.items():
            print(f"Processing {label} entities...")
            
            # 收集每个实体的所有别名
            entity_aliases = {}
            current_id = 1
            
            for alias, info in entities.items():
                # 如果没有entity_id，生成一个
                if 'entity_id' in info:
                    entity_id = info['entity_id']
                else:
                    # 生成唯一ID
                    while current_id in entity_aliases:
                        current_id += 1
                    entity_id = current_id
                    current_id += 1
                
                normalized_name = info.get('normalized_name', alias)
                
                if entity_id not in entity_aliases:
                    entity_aliases[entity_id] = {
                        'normalized_name': normalized_name,
                        'aliases': [alias]
                    }
                else:
                    entity_aliases[entity_id]['aliases'].append(alias)
            
            # 插入实体和别名
            for entity_id, info in entity_aliases.items():
                normalized_name = info['normalized_name']
                aliases = info['aliases']
                
                # 插入实体
                try:
                    cursor.execute('''
                    INSERT INTO entities (entity_id, name, label, normalized_name)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        name = VALUES(name),
                        label = VALUES(label),
                        normalized_name = VALUES(normalized_name),
                        updated_at = CURRENT_TIMESTAMP
                    ''', (entity_id, normalized_name, label, normalized_name))
                except Exception as e:
                    print(f"Error inserting entity {entity_id}: {str(e)}")
                    continue
                
                # 插入别名
                for alias in aliases:
                    try:
                        cursor.execute('''
                        INSERT INTO aliases (entity_id, alias_name)
                        VALUES (%s, %s)
                        ON DUPLICATE KEY UPDATE
                            entity_id = VALUES(entity_id)
                        ''', (entity_id, alias))
                    except Exception as e:
                        print(f"Error inserting alias {alias}: {str(e)}")
                        continue
        
        conn.commit()
        print("Entities and aliases populated successfully!")
    except Exception as e:
        print(f"Error populating entities: {str(e)}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def populate_patterns_from_file():
    """从entity_patterns.json填充patterns表"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 创建patterns表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS patterns (
            pattern_id INT AUTO_INCREMENT PRIMARY KEY,
            label VARCHAR(50) NOT NULL,
            pattern VARCHAR(255) NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_pattern_label (label)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')
        
        # 读取entity_patterns.json文件
        with open('entity_patterns.json', 'r', encoding='utf-8') as f:
            patterns_data = json.load(f)
        
        # 插入模式
        for pattern in patterns_data:
            label = pattern.get('label')
            pattern_text = pattern.get('pattern')
            
            try:
                cursor.execute('''
                INSERT INTO patterns (label, pattern)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE
                    label = VALUES(label)
                ''', (label, pattern_text))
            except Exception as e:
                print(f"Error inserting pattern {pattern_text}: {str(e)}")
                continue
        
        conn.commit()
        print("Patterns populated successfully!")
    except Exception as e:
        print(f"Error populating patterns: {str(e)}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def main():
    """主函数"""
    # 创建表结构
    create_entity_tables()
    
    # 填充实体和别名
    populate_entities_from_lexicon()
    
    # 填充模式
    populate_patterns_from_file()
    
    print("All data populated successfully!")

if __name__ == "__main__":
    main()
