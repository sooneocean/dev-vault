"""
Post Validator - SEO validation rules and field verification
Ensures all updates meet quality standards before deployment
"""

import re
import json
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Validation result for a single check"""

    is_valid: bool
    field: str
    current_value: any
    target_range: str
    error_message: str = None
    suggestion: str = None


class PostValidator:
    """
    Validates post fields against SEO best practices.
    Rules based on YOLO LAB SEO standards.
    """

    # SEO validation rules
    TITLE_MIN = 55
    TITLE_MAX = 65
    TITLE_OPTIMAL = 60

    DESCRIPTION_MIN = 155
    DESCRIPTION_MAX = 165
    DESCRIPTION_OPTIMAL = 160

    INTERNAL_LINK_MIN = 2
    IMAGE_ALT_COVERAGE = 100  # percent

    def __init__(self, strict_mode: bool = False):
        """
        Initialize validator.

        Args:
            strict_mode: If True, enforce all rules strictly.
                        If False, allow warnings.
        """
        self.strict_mode = strict_mode
        self.validation_errors: List[ValidationResult] = []
        self.validation_warnings: List[ValidationResult] = []

    def reset(self) -> None:
        """Clear validation results"""
        self.validation_errors = []
        self.validation_warnings = []

    def validate_title(self, title: str) -> ValidationResult:
        """
        Validate post title length.

        Title should be 55-65 characters (optimal ~60).
        Checks:
        - Length within range
        - No excessive punctuation
        - No excessive capitalization
        """
        if not title:
            return ValidationResult(
                is_valid=False,
                field="title",
                current_value=title,
                target_range=f"{self.TITLE_MIN}-{self.TITLE_MAX}",
                error_message="Title is empty",
            )

        length = len(title)
        is_valid = self.TITLE_MIN <= length <= self.TITLE_MAX

        result = ValidationResult(
            is_valid=is_valid,
            field="title",
            current_value=title,
            target_range=f"{self.TITLE_MIN}-{self.TITLE_MAX}",
        )

        if not is_valid:
            if length < self.TITLE_MIN:
                result.error_message = (
                    f"Title too short: {length} chars "
                    f"(min {self.TITLE_MIN})"
                )
                result.suggestion = "Add keywords or clarify the message"
            else:
                result.error_message = (
                    f"Title too long: {length} chars "
                    f"(max {self.TITLE_MAX})"
                )
                result.suggestion = "Remove non-essential words"

        return result

    def validate_description(
        self, description: str
    ) -> ValidationResult:
        """
        Validate meta description length.

        Description should be 155-165 characters (optimal ~160).
        Checks:
        - Length within range
        - Contains actionable CTA
        - No HTML tags
        """
        if not description:
            return ValidationResult(
                is_valid=False,
                field="excerpt",
                current_value=description,
                target_range=f"{self.DESCRIPTION_MIN}-{self.DESCRIPTION_MAX}",
                error_message="Description is empty",
            )

        # Remove HTML tags for length check
        clean_desc = re.sub(r"<[^>]+>", "", description)
        length = len(clean_desc)

        is_valid = (
            self.DESCRIPTION_MIN <= length <= self.DESCRIPTION_MAX
        )

        # Check for CTA keywords
        cta_keywords = [
            "搶票",
            "立即",
            "了解",
            "點擊",
            "查看",
            "購買",
            "預訂",
            "預購",
            "領取",
            "獲取",
        ]
        has_cta = any(kw in description for kw in cta_keywords)

        result = ValidationResult(
            is_valid=is_valid and has_cta,
            field="excerpt",
            current_value=description,
            target_range=f"{self.DESCRIPTION_MIN}-{self.DESCRIPTION_MAX}",
        )

        if not is_valid:
            if length < self.DESCRIPTION_MIN:
                result.error_message = (
                    f"Description too short: {length} chars "
                    f"(min {self.DESCRIPTION_MIN})"
                )
                result.suggestion = "Add more context and keywords"
            else:
                result.error_message = (
                    f"Description too long: {length} chars "
                    f"(max {self.DESCRIPTION_MAX})"
                )
                result.suggestion = "Trim to most important points"

        if not has_cta:
            result.error_message = (
                result.error_message or ""
            ) + " | Missing CTA"
            result.suggestion = (
                "Add call-to-action: 搶票、購買、了解等"
            )

        return result

    def validate_schema_json(
        self, content: str
    ) -> Tuple[bool, List[str]]:
        """
        Validate JSON-LD schema blocks in content.

        Returns:
            (is_valid, list of errors)
        """
        errors = []

        # Extract all JSON-LD blocks
        pattern = r'<script type="application/ld\+json">(.*?)</script>'
        schemas = re.findall(pattern, content, re.DOTALL)

        if not schemas:
            return True, []  # No schema is OK

        for schema_str in schemas:
            try:
                schema = json.loads(schema_str)

                # Validate required fields based on type
                schema_type = schema.get("@type", "")

                if schema_type == "FAQPage":
                    if "mainEntity" not in schema:
                        errors.append(
                            "FAQPage schema missing mainEntity"
                        )
                    for item in schema.get("mainEntity", []):
                        if "acceptedAnswer" not in item:
                            errors.append(
                                f"FAQ item missing acceptedAnswer: "
                                f"{item.get('name', 'unknown')}"
                            )

                elif schema_type == "BlogPosting":
                    required = [
                        "headline",
                        "datePublished",
                        "author",
                    ]
                    for field in required:
                        if field not in schema:
                            errors.append(
                                f"BlogPosting schema missing {field}"
                            )

            except json.JSONDecodeError as e:
                errors.append(f"Invalid JSON-LD schema: {e}")

        return len(errors) == 0, errors

    def validate_internal_links(
        self, content: str, valid_post_ids: List[int]
    ) -> ValidationResult:
        """
        Validate internal links in content.

        Checks:
        - Minimum number of internal links (≥2)
        - Links point to valid posts
        - No broken links

        Args:
            content: Post HTML content
            valid_post_ids: List of valid WordPress post IDs
        """
        # Extract all internal links
        pattern = r'href="([^"]*)"'
        links = re.findall(pattern, content)

        # Filter for internal links (WordPress post permalinks)
        internal_links = [
            link
            for link in links
            if "yololab.net" in link or "/posts/" in link
        ]

        # Extract post IDs from links
        found_post_ids = []
        for link in internal_links:
            # Try to extract post ID from permalink
            match = re.search(r"/p/(\d+)/", link) or re.search(
                r"\?p=(\d+)", link
            )
            if match:
                post_id = int(match.group(1))
                found_post_ids.append(post_id)

        # Validate
        is_valid = len(found_post_ids) >= self.INTERNAL_LINK_MIN

        broken_links = []
        if valid_post_ids:
            broken_links = [
                pid
                for pid in found_post_ids
                if pid not in valid_post_ids
            ]
            is_valid = is_valid and len(broken_links) == 0

        result = ValidationResult(
            is_valid=is_valid,
            field="content_internal_links",
            current_value=len(found_post_ids),
            target_range=f">= {self.INTERNAL_LINK_MIN}",
        )

        if not is_valid:
            if len(found_post_ids) < self.INTERNAL_LINK_MIN:
                result.error_message = (
                    f"Too few internal links: {len(found_post_ids)} "
                    f"(min {self.INTERNAL_LINK_MIN})"
                )
                result.suggestion = "Add relevant internal links"

            if broken_links:
                result.error_message = (
                    f"Broken internal links to posts: {broken_links}"
                )
                result.suggestion = "Remove or fix links to deleted posts"

        return result

    def validate_image_alt(self, content: str) -> ValidationResult:
        """
        Validate image alt text coverage.

        Checks:
        - All images have alt attribute
        - Alt text is not empty
        - Alt text is descriptive (> 5 chars)
        """
        # Extract all img tags
        img_pattern = r'<img[^>]*>'
        images = re.findall(img_pattern, content)

        images_without_alt = 0
        alt_too_short = 0

        for img in images:
            alt_match = re.search(r'alt="([^"]*)"', img)

            if not alt_match:
                images_without_alt += 1
            else:
                alt_text = alt_match.group(1)
                if len(alt_text) < 5:
                    alt_too_short += 1

        is_valid = (
            images_without_alt == 0 and alt_too_short == 0
        )

        result = ValidationResult(
            is_valid=is_valid,
            field="content_image_alt",
            current_value={
                "total_images": len(images),
                "missing_alt": images_without_alt,
                "alt_too_short": alt_too_short,
            },
            target_range=f"100% with descriptive alt",
        )

        if not is_valid:
            errors = []
            if images_without_alt > 0:
                errors.append(
                    f"{images_without_alt} images missing alt"
                )
            if alt_too_short > 0:
                errors.append(
                    f"{alt_too_short} images with short alt"
                )
            result.error_message = " | ".join(errors)
            result.suggestion = (
                "Add descriptive alt text to all images"
            )

        return result

    def validate_featured_image_alt(
        self, featured_image: Dict
    ) -> ValidationResult:
        """
        Validate featured image alt text.
        """
        result = ValidationResult(
            is_valid=True,
            field="featured_image_alt",
            current_value=None,
            target_range="Not empty",
        )

        if not featured_image:
            result.is_valid = False
            result.error_message = "No featured image"
            result.suggestion = "Add featured image with alt text"
            return result

        alt = featured_image.get("alt", "").strip()

        if not alt:
            result.is_valid = False
            result.error_message = "Featured image alt is empty"
            result.suggestion = "Add descriptive alt text"
        elif len(alt) < 5:
            result.is_valid = False
            result.error_message = (
                f"Featured image alt too short: '{alt}'"
            )
            result.suggestion = "Make alt text more descriptive"
        else:
            result.current_value = alt

        return result

    def validate_post(
        self,
        post: Dict,
        valid_post_ids: Optional[List[int]] = None,
    ) -> Tuple[bool, List[ValidationResult]]:
        """
        Validate entire post object.

        Returns:
            (all_valid, list of ValidationResults)
        """
        self.reset()
        results = []

        # Validate title
        title_result = self.validate_title(post.get("title", ""))
        results.append(title_result)
        if not title_result.is_valid:
            self.validation_errors.append(title_result)

        # Validate description (excerpt)
        desc_result = self.validate_description(
            post.get("excerpt", "")
        )
        results.append(desc_result)
        if not desc_result.is_valid:
            self.validation_errors.append(desc_result)

        # Validate schema
        content = post.get("content", "")
        schema_valid, schema_errors = self.validate_schema_json(
            content
        )
        if not schema_valid:
            for error in schema_errors:
                result = ValidationResult(
                    is_valid=False,
                    field="content_schema",
                    current_value=error,
                    target_range="Valid JSON-LD",
                    error_message=error,
                )
                results.append(result)
                self.validation_errors.append(result)

        # Validate internal links
        link_result = self.validate_internal_links(
            content, valid_post_ids or []
        )
        results.append(link_result)
        if not link_result.is_valid:
            self.validation_errors.append(link_result)

        # Validate image alt
        alt_result = self.validate_image_alt(content)
        results.append(alt_result)
        if not alt_result.is_valid:
            self.validation_warnings.append(alt_result)

        # Validate featured image alt
        featured_img = post.get("featured_image")
        if featured_img:
            img_alt_result = self.validate_featured_image_alt(
                featured_img
            )
            results.append(img_alt_result)
            if not img_alt_result.is_valid:
                self.validation_warnings.append(img_alt_result)

        # Determine overall validity
        all_valid = len(self.validation_errors) == 0
        if self.strict_mode:
            all_valid = all_valid and len(self.validation_warnings) == 0

        return all_valid, results

    def get_error_summary(self) -> Dict:
        """Get summary of validation errors"""
        return {
            "total_errors": len(self.validation_errors),
            "total_warnings": len(self.validation_warnings),
            "errors": [
                {
                    "field": e.field,
                    "message": e.error_message,
                    "suggestion": e.suggestion,
                }
                for e in self.validation_errors
            ],
            "warnings": [
                {
                    "field": w.field,
                    "message": w.error_message,
                    "suggestion": w.suggestion,
                }
                for w in self.validation_warnings
            ],
        }
