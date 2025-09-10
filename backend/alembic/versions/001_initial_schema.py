"""Initial database schema

Revision ID: 0001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create collections table
    op.create_table('collections',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create documents table
    op.create_table('documents',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('collection_id', sa.String(), nullable=False),
        sa.Column('source_type', sa.String(length=20), nullable=False),
        sa.Column('source_url', sa.String(length=1000), nullable=True),
        sa.Column('filename', sa.String(length=255), nullable=True),
        sa.Column('title', sa.String(length=500), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('meta', sa.JSON(), nullable=True),
        sa.Column('word_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['collection_id'], ['collections.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create chunks table
    op.create_table('chunks',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('document_id', sa.String(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('token_count', sa.Integer(), nullable=True),
        sa.Column('embedding_vector', sa.JSON(), nullable=True),
        sa.Column('meta', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create flashcards table
    op.create_table('flashcards',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('collection_id', sa.String(), nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('answer', sa.Text(), nullable=False),
        sa.Column('difficulty', sa.String(length=20), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('style', sa.String(length=20), nullable=True),
        sa.Column('source_chunk_ids', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['collection_id'], ['collections.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create reviews table
    op.create_table('reviews',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('flashcard_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=False),
        sa.Column('repetitions', sa.Integer(), nullable=True),
        sa.Column('interval_days', sa.Integer(), nullable=True),
        sa.Column('easiness_factor', sa.Float(), nullable=True),
        sa.Column('due_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('review_count', sa.Integer(), nullable=True),
        sa.Column('correct_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['flashcard_id'], ['flashcards.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create quiz_sessions table
    op.create_table('quiz_sessions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('collection_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=False),
        sa.Column('strategy', sa.String(length=20), nullable=True),
        sa.Column('total_questions', sa.Integer(), nullable=False),
        sa.Column('completed_questions', sa.Integer(), nullable=True),
        sa.Column('correct_answers', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['collection_id'], ['collections.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create quiz_questions table
    op.create_table('quiz_questions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('session_id', sa.String(), nullable=False),
        sa.Column('flashcard_id', sa.String(), nullable=False),
        sa.Column('question_index', sa.Integer(), nullable=False),
        sa.Column('user_answer', sa.Text(), nullable=True),
        sa.Column('is_correct', sa.Boolean(), nullable=True),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('answered_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['flashcard_id'], ['flashcards.id'], ),
        sa.ForeignKeyConstraint(['session_id'], ['quiz_sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_chunk_document', 'chunks', ['document_id'])
    op.create_index('idx_chunk_index', 'chunks', ['document_id', 'chunk_index'])
    op.create_index('idx_review_user_due', 'reviews', ['user_id', 'due_at'])
    op.create_index('idx_review_flashcard', 'reviews', ['flashcard_id'])
    op.create_index('idx_quiz_user', 'quiz_sessions', ['user_id'])
    op.create_index('idx_quiz_collection', 'quiz_sessions', ['collection_id'])
    op.create_index('idx_quiz_question_session', 'quiz_questions', ['session_id', 'question_index'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_quiz_question_session', table_name='quiz_questions')
    op.drop_index('idx_quiz_collection', table_name='quiz_sessions')
    op.drop_index('idx_quiz_user', table_name='quiz_sessions')
    op.drop_index('idx_review_flashcard', table_name='reviews')
    op.drop_index('idx_review_user_due', table_name='reviews')
    op.drop_index('idx_chunk_index', table_name='chunks')
    op.drop_index('idx_chunk_document', table_name='chunks')
    
    # Drop tables
    op.drop_table('quiz_questions')
    op.drop_table('quiz_sessions')
    op.drop_table('reviews')
    op.drop_table('flashcards')
    op.drop_table('chunks')
    op.drop_table('documents')
    op.drop_table('collections')
