from sqlalchemy.orm import Session

from app.models import Rule
from app.schemas.response import success
from app.schemas.rule import RuleForm


def list_rule(db: Session):
    rules = db.query(Rule).all()
    return success(rules)


def add_rule(db: Session, rule_form: RuleForm):
    rule = Rule(**rule_form.model_dump(exclude={"id"}))
    db.add(rule)
    return success(rule)


def update_rule(db: Session, rule_form: RuleForm):
    rule = db.get(Rule, rule_form.id)
    if not rule:
        rule.section = rule_form.section
        rule.category = rule_form.category
        rule.regex = rule_form.regex
        rule.downloader = rule_form.downloader
        rule.save_path = rule_form.save_path
    return success()


def delete_rule(db: Session, rule_id):
    rule = db.get(Rule, rule_id)
    db.delete(rule)
    return success()
