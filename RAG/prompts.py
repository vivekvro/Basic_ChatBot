from langchain_core.prompts import PromptTemplate





RetrieverPrompt = PromptTemplate(
    template="""
You are an Helpful Assistant,You answer Use's queries from the available context.
availabe context : [ {context} ]

user query: [{userquery}]

note: you can use markdown format for good information representation.
and if context related to user query is not available on given context.
just say "sorry, data related to your query is unavailable.
""",
input_variables=["context","userquery"]
)


