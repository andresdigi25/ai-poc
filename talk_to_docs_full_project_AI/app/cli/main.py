import click
import asyncio
from loguru import logger
from app.core.document_processor import DocumentProcessor
from app.core.config import settings
import os

@click.group()
def cli():
    """Talk to Docs CLI tool."""
    pass

@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--output-dir', '-o', default='output', help='Output directory for processed files')
def process(file_path: str, output_dir: str):
    """Process a single document."""
    try:
        os.makedirs(output_dir, exist_ok=True)
        processor = DocumentProcessor()
        
        click.echo(f"Processing document: {file_path}")
        result = asyncio.run(processor.process_document(file_path))
        
        # Save results
        output_file = os.path.join(output_dir, f"{os.path.basename(file_path)}_processed.txt")
        with open(output_file, 'w') as f:
            f.write(f"Summary:\n{result['summary']}\n\n")
            f.write(f"Full Text:\n{result['text_content']}\n")
        
        click.echo(f"Processing complete. Results saved to: {output_file}")
        click.echo(f"Extracted {len(result['images'])} images to: {output_dir}")
        
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        click.echo(f"Error: {str(e)}", err=True)

@cli.command()
@click.argument('directory', type=click.Path(exists=True))
@click.option('--output-dir', '-o', default='output', help='Output directory for processed files')
def batch_process(directory: str, output_dir: str):
    """Process all PDF files in a directory."""
    try:
        os.makedirs(output_dir, exist_ok=True)
        processor = DocumentProcessor()
        
        pdf_files = [f for f in os.listdir(directory) if f.lower().endswith('.pdf')]
        if not pdf_files:
            click.echo("No PDF files found in the specified directory.")
            return
        
        click.echo(f"Found {len(pdf_files)} PDF files to process.")
        
        for pdf_file in pdf_files:
            file_path = os.path.join(directory, pdf_file)
            click.echo(f"\nProcessing: {pdf_file}")
            
            try:
                result = asyncio.run(processor.process_document(file_path))
                
                # Save results
                output_file = os.path.join(output_dir, f"{pdf_file}_processed.txt")
                with open(output_file, 'w') as f:
                    f.write(f"Summary:\n{result['summary']}\n\n")
                    f.write(f"Full Text:\n{result['text_content']}\n")
                
                click.echo(f"✓ Completed: {pdf_file}")
                click.echo(f"  - Summary saved to: {output_file}")
                click.echo(f"  - Extracted {len(result['images'])} images")
                
            except Exception as e:
                logger.error(f"Error processing {pdf_file}: {str(e)}")
                click.echo(f"✗ Error processing {pdf_file}: {str(e)}", err=True)
        
    except Exception as e:
        logger.error(f"Error in batch processing: {str(e)}")
        click.echo(f"Error: {str(e)}", err=True)

if __name__ == '__main__':
    cli() 