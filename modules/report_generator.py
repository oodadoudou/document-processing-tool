import logging
import time
import os

logger = logging.getLogger(__name__)

if not logger.handlers:
    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

REPORT_TEMPLATE = """
╔══════════════ {title} ═════════════════╗
║ Total Files Processed: {total}
║ Successfully Renamed: {success}
╚════════════════════════════════════════╝
"""

def generate_report(report_title: str, total_processed: int, success_files: list, error_files: list, duration: float, output_file: str = None) -> None:
    """
    Generates a formatted operation report and logs it.
    Args:
        report_title (str): Report title
        total_processed (int): Total number of files processed
        success_files (list): List of successful files
        error_files (list): List of failed files, where each element is a (filename, error reason) tuple
        duration (float): Time taken for the operation (seconds)
        output_file (str, optional): Output file path
    """
    success_count = len(success_files)
    error_count = len(error_files)
    success_rate = (success_count / total_processed) * 100 if total_processed else 0

    # Build report header
    report = fr"""
    {report_title}
    Output File: {output_file.ljust(30) if output_file else "N/A"}
    Total Files Processed: {total_processed:<5}
    Successful Files: {success_count:<5}
    Failed Files: {error_count:<5}
    Success Rate: {success_rate:.2f}%
    Duration: {duration:.2f} seconds
    {"─" * 50}
    Failure Details:
    """

    # Process failed file information
    if error_files:
        for idx, (fname, reason) in enumerate(error_files, 1):
            report += f"{idx:02d}. {fname[:30]:<30} | {reason[:40]}\n"
        report += "For more error details, please check the log."
    else:
        report += "✓ All files processed successfully."

    # Output report
    logger.info(report)

    # Optionally write to a file
    if output_file:
        try:
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"Report saved to: {output_file}")
        except Exception as e:
            logger.error(f"Failed to save report to file '{output_file}': {e}")


def generate_merge_report(output_name: str, files: list, success_files: list, error_files: list, start_time: float) -> None:
    """
    Generates a merge report.
    Args:
        output_name (str): The name of the merged output file.
        files (list): List of all files considered for merging.
        success_files (list): List of files successfully merged.
        error_files (list): List of files that failed to merge.
        start_time (float): The timestamp when the merge operation started.
    """
    duration = time.time() - start_time
    report = f"""
Output File: {output_name.ljust(30)}
Total Files Processed: {len(files):<5}
Successfully Merged: {len(success_files):<5}
Failed Files: {len(error_files):<5}
Duration: {duration:.2f} seconds
{"─" * 50}
Failure Details:
    """
    if error_files:
        for idx, (fname, reason) in enumerate(error_files, 1):
            report += f"{idx:02d}. {fname[:30]:<30} | {reason[:40]}\n"
        report += "For more error details, please check the log."
    else:
        report += "✓ All files merged successfully."
    logger.info(report)


def generate_partial_report(success_files: list, error_files: list, exception: Exception) -> None:
    """
    Generates a report for abnormal termination of an operation.
    Args:
        success_files (list): List of files successfully processed before termination.
        error_files (list): List of files that failed before termination.
        exception (Exception): The exception that caused the abnormal termination.
    """
    partial_report = f"""
Files Processed: {len(success_files)}
Failed Files: {len(error_files)}
Error Reason: {str(exception)[:50]}
    """
    logger.error(partial_report)